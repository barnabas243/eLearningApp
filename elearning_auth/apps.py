from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "elearning_auth"  # unique name. auth is already used by django
    verbose_name = "eLearningApp Auth"
