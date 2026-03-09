from django.apps import AppConfig


class GestionBonanaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.gestion_bonana'
    verbose_name = "Gestion du Personnel"

    def ready(self):
        """
        Méthode appelée lorsque l'application est prête
        """
        # Importez et enregistrez les signaux
        import applications.gestion_bonana.signals








    