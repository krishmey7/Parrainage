from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    Personnel,
    ObjectifPersonnel,
    PostulerObjectif,
    PerformancePersonnel,
    FilleulPersonnel,
    PrimePersonnel
)


# ================================
#   PERSONNEL
# ================================
@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = (
        'utilisateur',
        'matricule',
        'poste',
        'statut',
        'date_embauche',
        'salaire_base',
        'date_creation'
    )
    list_filter = ('statut', 'poste', 'date_embauche')
    search_fields = ('utilisateur__username', 'utilisateur__email', 'matricule')
    readonly_fields = ('date_creation', 'date_modification', 'anciennete_mois')

    fieldsets = (
        ("Information personnelle", {
            "fields": ('utilisateur', 'matricule', 'poste', 'statut')
        }),
        ("Contacts & Pro", {
            "fields": ('telephone_pro', 'email_pro', 'date_embauche', 'salaire_base')
        }),
        ("Suivi", {
            "fields": ('date_creation', 'date_modification', 'anciennete_mois')
        }),
    )


# ================================
#   OBJECTIFS PERSONNEL
# ================================
@admin.register(ObjectifPersonnel)
class ObjectifPersonnelAdmin(admin.ModelAdmin):
    list_display = (
        'intitule',
        'date_debut',
        'date_fin',
        'periodicite',
        'nombre_filleuls_requis',
        'prime_objectif',
        'est_actif',
        'est_en_cours',
        'nombre_postulants',
        'nombre_acceptes'
    )
    list_filter = ('periodicite', 'est_actif', 'date_debut')
    search_fields = ('intitule',)
    filter_horizontal = ('produits_eligibles',)


# ================================
#   POSTULER OBJECTIF
# ================================
@admin.register(PostulerObjectif)
class PostulerObjectifAdmin(admin.ModelAdmin):
    list_display = (
        'personnel',
        'objectif',
        'statut',
        'date_postulation',
        'date_validation'
    )
    list_filter = ('statut', 'date_postulation')
    search_fields = ('personnel__utilisateur__username', 'objectif__intitule')


# ================================
#   PERFORMANCE PERSONNEL
# ================================
@admin.register(PerformancePersonnel)
class PerformancePersonnelAdmin(admin.ModelAdmin):
    list_display = (
        'personnel',
        'objectif',
        'nombre_filleuls_parraines',
        'nombre_filleuls_qualifies',
        'statut',
        'prime_recue',
        'progression_pourcentage',
        'date_debut_suivi'
    )
    list_filter = ('statut', 'prime_recue', 'date_debut_suivi')
    search_fields = ('postulation__personnel__utilisateur__username', 'postulation__objectif__intitule')
    readonly_fields = ('progression_pourcentage', 'objectif', 'personnel')


# ================================
#   FILLEUL PERSONNEL
# ================================
@admin.register(FilleulPersonnel)
class FilleulPersonnelAdmin(admin.ModelAdmin):
    list_display = (
        'performance',
        'filleul',
        'achat_filleul',
        'est_eligible',
        'produit_achete',
        'montant_achat',
        'date_parrainage'
    )
    list_filter = ('est_eligible', 'date_parrainage')
    search_fields = ('filleul__username', 'performance__postulation__personnel__utilisateur__username')


# ================================
#   PRIME PERSONNEL
# ================================
@admin.register(PrimePersonnel)
class PrimePersonnelAdmin(admin.ModelAdmin):
    list_display = (
        'personnel',
        'objectif',
        'montant_prime',
        'nombre_filleuls_qualifies',
        'transaction_associee',
        'date_versement'
    )
    list_filter = ('date_versement',)
    search_fields = ('personnel__utilisateur__username', 'objectif__intitule')
