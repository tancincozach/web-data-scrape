from django.apps import AppConfig


class ClientManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.client_management"

    def ready(self):
        # Register the drf-spectacular authentication extension.
        import app.client_management.schema  # noqa: F401
