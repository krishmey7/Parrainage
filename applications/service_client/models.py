from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Requete(models.Model):
    STATUT_CHOICES = [
        ('non_traite', 'Non traité'),
        ('en_cours', 'En cours de traitement'),
        ('traite', 'Traité'),
    ]
    
    PRIORITE_CHOICES = [
        ('faible', 'Faible'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]
    
    # Informations de base
    nom_complet = models.CharField(max_length=100, verbose_name="Nom complet", default="")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone", default="")
    titre = models.CharField(max_length=200, verbose_name="Titre de la requête")
    description = models.TextField(verbose_name="Description détaillée")
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='normale', verbose_name="Priorité")
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='non_traite', verbose_name="Statut")
    
    # Relations
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Utilisateur")
    assigne_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='requetes_assignees', verbose_name="Assigné à")
    
    # Dates
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    date_fermeture = models.DateTimeField(null=True, blank=True, verbose_name="Date de fermeture")
    
    # Métadonnées
    categorie = models.CharField(max_length=50, blank=True, verbose_name="Catégorie")
    
    class Meta:
        verbose_name = "Requête"
        verbose_name_plural = "Requêtes"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"#{self.id} - {self.titre} ({self.get_statut_display()})"

class Reponse(models.Model):
    requete = models.ForeignKey(Requete, on_delete=models.CASCADE, related_name='reponses', verbose_name="Requête")
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Auteur")
    message = models.TextField(verbose_name="Message")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    est_interne = models.BooleanField(default=False, verbose_name="Note interne (non visible par le client)")
    
    class Meta:
        verbose_name = "Réponse"
        verbose_name_plural = "Réponses"
        ordering = ['date_creation']
    
    def __str__(self):
        return f"Réponse à #{self.requete.id} par {self.auteur.username}"

class PieceJointe(models.Model):
    requete = models.ForeignKey(Requete, on_delete=models.CASCADE, related_name='pieces_jointes', verbose_name="Requête")
    fichier = models.FileField(upload_to='pieces_jointes/', verbose_name="Fichier")
    nom_original = models.CharField(max_length=255, verbose_name="Nom original")
    date_upload = models.DateTimeField(auto_now_add=True, verbose_name="Date d'upload")
    
    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"
    
    def __str__(self):
        return f"{self.nom_original} - {self.requete.titre}"
