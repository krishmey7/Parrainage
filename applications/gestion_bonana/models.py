from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import datetime, date
import random

# personnel/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import datetime, date
import random

class PersonnelManager(models.Manager):
    def get_for_user(self, user):
        """
        Retourne le profil Personnel pour un utilisateur.
        Le crée automatiquement s'il n'existe pas.
        """
        try:
            return self.get(utilisateur=user)
        except self.model.DoesNotExist:
            # Création automatique avec matricule généré
            personnel = self.create(
                utilisateur=user,
                poste='Collaborateur',
                date_embauche=date.today(),
                salaire_base=Decimal('0.00')
            )
            return personnel

class Personnel(models.Model):
    STATUT_CHOIX = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('congé', 'En congé'),
    ]

    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='personnel',
        verbose_name="Utilisateur associé"
    )

    matricule = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name="Matricule du personnel"
    )

    poste = models.CharField(
        max_length=100, 
        verbose_name="Poste occupé", 
        default='Collaborateur'
    )
    
    date_embauche = models.DateField(
        verbose_name="Date d'embauche",
        default=date.today
    )
    
    salaire_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Salaire de base"
    )
    
    statut = models.CharField(
        max_length=10, 
        choices=STATUT_CHOIX, 
        default='actif', 
        verbose_name="Statut professionnel"
    )
    
    telephone_pro = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Téléphone professionnel"
    )
    
    email_pro = models.EmailField(
        blank=True, 
        null=True, 
        verbose_name="Email professionnel"
    )
    
    date_creation = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Date de création"
    )
    
    date_modification = models.DateTimeField(
        auto_now=True, 
        verbose_name="Date de modification"
    )

    objects = PersonnelManager()

    class Meta:
        verbose_name = "Membre du personnel"
        verbose_name_plural = "Membres du personnel"
        ordering = ['-date_creation']

    def __str__(self):
        full_name = self.utilisateur.get_full_name()
        return f"{full_name if full_name else self.utilisateur.username} - {self.poste} ({self.matricule})"

    @property
    def anciennete_mois(self):
        """Calcule l'ancienneté en mois"""
        aujourdhui = date.today()
        mois_ecoules = (aujourdhui.year - self.date_embauche.year) * 12 + (aujourdhui.month - self.date_embauche.month)
        return max(0, mois_ecoules)

    def save(self, *args, **kwargs):
        if not self.matricule:
            self.matricule = self.generer_matricule()
        
        if not self.email_pro and self.utilisateur.email:
            self.email_pro = self.utilisateur.email
            
        super().save(*args, **kwargs)

    def generer_matricule(self):
        """Génère un matricule unique automatiquement"""
        prefixe = "MAT"
        chiffre = random.randint(10000, 99999)
        matricule_propose = f"{prefixe}-{chiffre}"

        while Personnel.objects.filter(matricule=matricule_propose).exists():
            chiffre = random.randint(10000, 99999)
            matricule_propose = f"{prefixe}-{chiffre}"
        return matricule_propose

    @classmethod
    def get_or_create_for_user(cls, user):
        """Méthode de classe pour obtenir ou créer un Personnel"""
        return cls.objects.get_for_user(user)




class ObjectifPersonnel(models.Model):
    PERIODICITE_CHOIX = [
        ('journalier', 'Journalier'),
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('semestriel', 'Semestriel'),
        ('annuel', 'Annuel'),
    ]

    intitule = models.CharField(
        max_length=200,
        verbose_name="Intitulé de l'objectif"
    )

    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")

    periodicite = models.CharField(
        max_length=15,
        choices=PERIODICITE_CHOIX,
        default='mensuel',
        verbose_name="Périodicité"
    )

    nombre_filleuls_requis = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de filleuls requis"
    )

    filleuls_doivent_acheter = models.BooleanField(
        default=True,
        verbose_name="Les filleuls doivent effectuer un achat"
    )

    produits_eligibles = models.ManyToManyField(
        'produits.Produit',
        blank=True,
        related_name='objectifs_personnel',
        verbose_name="Produits éligibles",
        help_text="Produits que les filleuls doivent acheter (laisser vide pour tous les produits)"
    )

    prime_objectif = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Prime pour objectif atteint",
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    est_actif = models.BooleanField(
        default=True,
        verbose_name="Objectif actif"
    )

    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Objectif personnel"
        verbose_name_plural = "Objectifs du personnel"
        ordering = ['-date_creation']

    def __str__(self):
        return f"Objectif {self.intitule} ({self.date_debut} - {self.date_fin})"

    @property
    def est_en_cours(self):
        """Vérifie si l'objectif est en cours"""
        aujourdhui = date.today()
        return self.date_debut <= aujourdhui <= self.date_fin and self.est_actif

    @property
    def nombre_postulants(self):
        """Retourne le nombre de personnels ayant postulé"""
        return self.postulations.count()

    @property
    def nombre_acceptes(self):
        """Retourne le nombre de postulations acceptées"""
        return self.postulations.filter(statut='accepte').count()


class PostulerObjectif(models.Model):
    STATUT_CHOIX = [
        ('en_attente', 'En attente de validation'),
        ('accepte', 'Accepté'),
        ('rejete', 'Rejeté'),
    ]

    personnel = models.ForeignKey(
        Personnel,
        on_delete=models.CASCADE,
        related_name='postulations',
        verbose_name="Personnel"
    )

    objectif = models.ForeignKey(
        ObjectifPersonnel,
        on_delete=models.CASCADE,
        related_name='postulations',
        verbose_name="Objectif"
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOIX,
        default='accepte',
        verbose_name="Statut de la candidature"
    )

    date_postulation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de postulation"
    )

    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation"
    )

    class Meta:
        verbose_name = "Postulation à un objectif"
        verbose_name_plural = "Postulations aux objectifs"
        unique_together = ['personnel', 'objectif']
        ordering = ['-date_postulation']

    def __str__(self):
        return f"{self.personnel} -> {self.objectif} [{self.statut}]"

    @property
    def peut_postuler(self):
        """Vérifie si on peut encore postuler à cet objectif"""
        return self.objectif.est_en_cours and self.objectif.est_actif


class PerformancePersonnel(models.Model):
    STATUT_CHOIX = [
        ('en_cours', 'En cours'),
        ('atteint', 'Objectif atteint'),
        ('non_atteint', 'Objectif non atteint'),
        ('prime_payee', 'Prime payée'),
    ]

    postulation = models.OneToOneField(
        "PostulerObjectif",
        on_delete=models.CASCADE,
        related_name="performance",
        verbose_name="Postulation"
    )

    nombre_filleuls_parraines = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de filleuls parrainés"
    )

    nombre_filleuls_qualifies = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de filleuls qualifiés"
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOIX,
        default='en_cours',
        verbose_name="Statut de performance"
    )

    prime_recue = models.BooleanField(
        default=False,
        verbose_name="Prime reçue"
    )

    date_prime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de versement de la prime"
    )

    date_debut_suivi = models.DateTimeField(auto_now_add=True, verbose_name="Début du suivi")
    date_mise_a_jour = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        verbose_name = "Performance du personnel"
        verbose_name_plural = "Performances du personnel"
        ordering = ['-date_debut_suivi']

    def __str__(self):
        return f"Performance {self.personnel} -> {self.objectif} ({self.statut})"

    @property
    def personnel(self):
        return self.postulation.personnel

    @property
    def objectif(self):
        return self.postulation.objectif

    @property
    def objectif_atteint(self):
        """Vérifie si l'objectif est atteint"""
        return self.nombre_filleuls_qualifies >= self.objectif.nombre_filleuls_requis

    @property
    def progression_pourcentage(self):
        """Pourcentage d'avancement"""
        requis = self.objectif.nombre_filleuls_requis
        if requis == 0:
            return 100
        return min(100, int((self.nombre_filleuls_qualifies / requis) * 100))

    def mettre_a_jour_statut(self):
        """Met à jour automatiquement le statut selon la progression"""
        if self.objectif_atteint:
            self.statut = 'atteint'
        else:
            self.statut = 'en_cours'
        self.save()


class FilleulPersonnel(models.Model):
    performance = models.ForeignKey(
        PerformancePersonnel,
        on_delete=models.CASCADE,
        related_name='filleuls',
        verbose_name="Performance"
    )

    filleul = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parrainages_personnel',
        verbose_name="Filleul parrainé"
    )

    achat_filleul = models.ForeignKey(
        'produits.Achat',
        on_delete=models.CASCADE,
        related_name='parrainages_personnel',
        verbose_name="Achat du filleul"
    )

    est_eligible = models.BooleanField(
        default=False,
        verbose_name="Est éligible pour l'objectif"
    )

    date_parrainage = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de parrainage"
    )

    date_qualification = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de qualification"
    )

    produit_achete = models.ForeignKey(
        'produits.Produit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Produit acheté"
    )

    montant_achat = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant du contrat"
    )

    class Meta:
        verbose_name = "Filleul du personnel"
        verbose_name_plural = "Filleuls du personnel"
        unique_together = ['performance', 'filleul', 'achat_filleul']

    def __str__(self):
        return f"Filleul: {self.filleul.email} - Parrain: {self.performance.personnel}"


class PrimePersonnel(models.Model):
    personnel = models.ForeignKey(
        Personnel,
        on_delete=models.CASCADE,
        related_name='primes',
        verbose_name="Membre du personnel"
    )

    objectif = models.ForeignKey(
        ObjectifPersonnel,
        on_delete=models.CASCADE,
        verbose_name="Objectif"
    )

    montant_prime = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Montant de la prime"
    )

    transaction_associee = models.ForeignKey(
        'portefeuille.TransactionPortefeuille',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Transaction associée"
    )

    nombre_filleuls_qualifies = models.PositiveIntegerField(
        verbose_name="Nombre de filleuls qualifiés"
    )

    date_versement = models.DateTimeField(auto_now_add=True, verbose_name="Date de versement")

    class Meta:
        verbose_name = "Prime du personnel"
        verbose_name_plural = "Primes du personnel"
        ordering = ['-date_versement']

    def __str__(self):
        return f"Prime {self.montant_prime} FC - {self.personnel}"