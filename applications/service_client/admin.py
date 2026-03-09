from django.contrib import admin
from .models import Requete, Reponse, PieceJointe

@admin.register(Requete)
class RequeteAdmin(admin.ModelAdmin):
    list_display = ['id', 'titre', 'utilisateur', 'statut', 'priorite', 'categorie', 'date_creation']
    list_filter = ['statut', 'priorite', 'categorie', 'date_creation']
    search_fields = ['titre', 'description', 'utilisateur__username', 'utilisateur__email']
    list_editable = ['statut', 'priorite']
    readonly_fields = ['date_creation', 'date_modification']
    date_hierarchy = 'date_creation'

    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'description', 'categorie', 'priorite')
        }),
        ('Gestion', {
            'fields': ('utilisateur', 'assigne_a', 'statut')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification', 'date_fermeture'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('utilisateur', 'assigne_a')

@admin.register(Reponse)
class ReponseAdmin(admin.ModelAdmin):
    list_display = ['id', 'requete', 'auteur', 'date_creation', 'est_interne']
    list_filter = ['est_interne', 'date_creation', 'auteur']
    search_fields = ['message', 'requete__titre', 'auteur__username']
    readonly_fields = ['date_creation']
    date_hierarchy = 'date_creation'

    fieldsets = (
        ('Contenu', {
            'fields': ('requete', 'auteur', 'message')
        }),
        ('Options', {
            'fields': ('est_interne',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('requete', 'auteur')

"""@admin.register(PieceJointe)
class PieceJointeAdmin(admin.ModelAdmin):
    list_display = ['id', 'nom_original', 'requete', 'date_upload']
    list_filter = ['date_upload']
    search_fields = ['nom_original', 'requete__titre']
    readonly_fields = ['date_upload']
    date_hierarchy = 'date_upload'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('requete')"""
