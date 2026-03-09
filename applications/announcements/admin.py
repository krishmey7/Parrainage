from django.contrib import admin
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "is_public", "recipient", "created_at")
    list_filter = ("is_public", "created_at")
    search_fields = ("title", "content", "recipient__username")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {
            "fields": ("title", "content")
        }),
        ("Type d’annonce", {
            "fields": ("is_public", "recipient"),
            "description": "Cochez 'Annonce publique' pour la rendre visible à tous. Sinon, choisissez un destinataire pour une annonce personnelle."
        }),
        ("Informations système", {
            "fields": ("created_at",),
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Validation logique :
        - Si annonce publique → pas de destinataire
        - Si annonce personnelle → destinataire obligatoire
        """
        if obj.is_public:
            obj.recipient = None
        elif not obj.recipient:
            raise ValueError("Vous devez spécifier un destinataire pour une annonce personnelle.")
        super().save_model(request, obj, form, change)
