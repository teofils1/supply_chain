from django.apps import AppConfig


class SupplychainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "supplychain"

    def ready(self):
        """Import signals when the app is ready."""
        import supplychain.signals  # noqa: F401
