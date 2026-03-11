from django.contrib import admin
from .models import BonusParrainage


@admin.register(BonusParrainage)
class BonusParrainageAdmin(admin.ModelAdmin):
    list_display = (
        "parrain",
        "filleul",
        "achat",
        "montant",
        "pourcentage",
        "est_premier_achat",
        "cree_le",
    )
    list_filter = ("est_premier_achat", "cree_le")
    search_fields = ("parrain__email", "filleul__email", "achat__id")
    ordering = ("-cree_le",)
    readonly_fields = ("cree_le",)

    fieldsets = (
        ("Informations Parrainage", {
            "fields": ("parrain", "filleul", "achat"),
        }),
        ("Bonus", {
            "fields": ("montant", "pourcentage", "est_premier_achat"),
        }),
        ("Suivi", {
            "fields": ("cree_le",),
        }),
    )
