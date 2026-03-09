# gestion_bonanan/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
import logging
from django.db.models.signals import post_save, pre_save, m2m_changed


from applications.produits.models import Achat
from applications.comptes.models import ProfilUtilisateur
from .models import Personnel, ObjectifPersonnel, PerformancePersonnel, FilleulPersonnel, PostulerObjectif

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Achat)
def suivre_parrainage_personnel(sender, instance, created, **kwargs):
    """
    Signal automatique pour suivre les parrainages du personnel
    Se déclenche après chaque achat pour lier les filleuls au personnel
    """
    if created:
        utilisateur_acheteur = instance.utilisateur
        achat = instance
        
        try:
            # Vérifier si l'acheteur a un parrain
            profil_acheteur = utilisateur_acheteur.profil
            parrain = profil_acheteur.parrain
            
            if parrain:
                # Vérifier si le parrain fait partie du personnel
                try:
                    personnel_parrain = parrain.personnel
                    
                    # Récupérer les objectifs actifs du personnel
                    objectifs_actifs = ObjectifPersonnel.objects.filter(
                        est_actif=True,
                        date_debut__lte=timezone.now().date(),
                        date_fin__gte=timezone.now().date()
                    )
                    
                    for objectif in objectifs_actifs:
                        # Vérifier si le personnel a postulé et été accepté pour cet objectif
                        try:
                            postulation = PostulerObjectif.objects.get(
                                personnel=personnel_parrain,
                                objectif=objectif,
                                statut='accepte'
                            )
                            
                            # Vérifier l'éligibilité du filleul
                            est_eligible = True
                            
                            if objectif.filleuls_doivent_acheter:
                                # Vérifier les produits éligibles si spécifiés
                                if objectif.produits_eligibles.exists():
                                    if achat.produit not in objectif.produits_eligibles.all():
                                        est_eligible = False
                            else:
                                # Si les filleuls ne doivent pas nécessairement acheter
                                est_eligible = True
                            
                            # Créer ou récupérer la performance
                            performance, created_perf = PerformancePersonnel.objects.get_or_create(
                                postulation=postulation,
                                defaults={
                                    'nombre_filleuls_parraines': 0,
                                    'nombre_filleuls_qualifies': 0,
                                    'statut': 'en_cours'
                                }
                            )
                            
                            # Vérifier si ce filleul n'est pas déjà enregistré pour cette performance
                            filleul_existe = FilleulPersonnel.objects.filter(
                                performance=performance,
                                filleul=utilisateur_acheteur,
                                achat_filleul=achat
                            ).exists()
                            
                            if not filleul_existe:
                                # Créer le lien filleul-personnel
                                filleul_personnel = FilleulPersonnel.objects.create(
                                    performance=performance,
                                    filleul=utilisateur_acheteur,
                                    achat_filleul=achat,
                                    produit_achete=achat.produit,
                                    montant_achat=achat.prix_au_moment_achat,
                                    est_eligible=est_eligible
                                )
                                
                                # Mettre à jour les compteurs de performance
                                performance.nombre_filleuls_parraines = FilleulPersonnel.objects.filter(
                                    performance=performance
                                ).count()
                                
                                performance.nombre_filleuls_qualifies = FilleulPersonnel.objects.filter(
                                    performance=performance,
                                    est_eligible=True
                                ).count()
                                
                                if est_eligible:
                                    filleul_personnel.date_qualification = timezone.now()
                                    filleul_personnel.save()
                                
                                # Vérifier si l'objectif est atteint
                                if performance.objectif_atteint and performance.statut == 'en_cours':
                                    performance.statut = 'atteint'
                                
                                performance.save()
                                
                                logger.info(f"Filleul {utilisateur_acheteur.email} ajouté à la performance de {personnel_parrain}")
                        
                        except PostulerObjectif.DoesNotExist:
                            # Le personnel n'a pas postulé ou n'a pas été accepté pour cet objectif
                            continue
                
                except Personnel.DoesNotExist:
                    # Le parrain n'est pas du personnel, on ignore
                    logger.debug(f"Le parrain {parrain.email} n'est pas du personnel")
                    pass
                    
        except ProfilUtilisateur.DoesNotExist:
            # L'acheteur n'a pas de profil, donc pas de parrain
            logger.debug(f"L'utilisateur {utilisateur_acheteur.email} n'a pas de profil")
            pass
        except Exception as e:
            logger.error(f"Erreur dans suivre_parrainage_personnel: {e}")

@receiver(post_save, sender=ObjectifPersonnel)
def creer_performance_automatique(sender, instance, created, **kwargs):
    """
    Crée automatiquement un suivi de performance pour chaque nouvel objectif
    uniquement pour les personnels qui ont postulé et été acceptés
    """
    if created:
        # Pour les nouvelles performances, elles seront créées quand les personnels postuleront
        logger.info(f"Nouvel objectif créé: {instance.intitule}")

@receiver(post_save, sender=PostulerObjectif)
def gerer_performance_postulation(sender, instance, created, **kwargs):
    """
    Gère la création/suppression des performances quand une postulation change de statut
    """
    if instance.statut == 'accepte':
        # Créer la performance si elle n'existe pas
        performance, created_perf = PerformancePersonnel.objects.get_or_create(
            postulation=instance,
            defaults={
                'nombre_filleuls_parraines': 0,
                'nombre_filleuls_qualifies': 0,
                'statut': 'en_cours'
            }
        )
        if created_perf:
            logger.info(f"Performance créée pour la postulation {instance.id}")
    elif instance.statut in ['rejete', 'en_attente']:
        # Supprimer la performance si elle existe
        PerformancePersonnel.objects.filter(postulation=instance).delete()
        logger.info(f"Performance supprimée pour la postulation {instance.id}")

@receiver(post_save, sender=FilleulPersonnel)
def mettre_a_jour_performance_filleul(sender, instance, created, **kwargs):
    """
    Met à jour automatiquement les compteurs de performance quand un filleul est modifié
    """
    if created or instance.tracker.has_changed('est_eligible'):
        try:
            performance = instance.performance
            
            # Recalculer les totaux exacts
            performance.nombre_filleuls_parraines = FilleulPersonnel.objects.filter(
                performance=performance
            ).count()
            
            performance.nombre_filleuls_qualifies = FilleulPersonnel.objects.filter(
                performance=performance,
                est_eligible=True
            ).count()
            
            # Mettre à jour le statut
            if performance.objectif_atteint:
                performance.statut = 'atteint'
            else:
                performance.statut = 'en_cours'
            
            performance.save()
            
            logger.debug(f"Performance {performance.id} mise à jour: {performance.nombre_filleuls_qualifies}/{performance.objectif.nombre_filleuls_requis}")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour performance filleul: {e}")

# DESACTIVER LES OBJET

@receiver(pre_save, sender=ObjectifPersonnel)
def desactiver_anciens_objectifs(sender, instance, **kwargs):
    """
    Désactive automatiquement les objectifs dont la date de fin est dépassée.
    """
    if instance.pk and instance.date_fin < timezone.now().date():
        instance.est_actif = False
        logger.debug(f"Objectif {instance.id} désactivé automatiquement (date fin dépassée)")