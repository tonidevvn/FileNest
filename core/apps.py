"""Core app configuration."""
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        """Perform initialization when Django starts."""
        pass  # Add any startup initialization here if needed
