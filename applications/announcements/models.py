from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

class Announcement(models.Model):
    """
    Modèle représentant une annonce publique ou personnelle.
    """
    title = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    content = models.TextField(
        verbose_name="Contenu"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Annonce publique ?"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="announcements",
        verbose_name="Destinataire (si personnel)"
    )

    class Meta:
        verbose_name = "Annonce"
        verbose_name_plural = "Annonces"
        ordering = ['-created_at']

    def __str__(self):
        if self.is_public:
            return f"[Publique] {self.title}"
        elif self.recipient:
            return f"[Perso → {self.recipient.username}] {self.title}"
        return self.title
