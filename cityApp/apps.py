from django.apps import AppConfig


class CityappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cityApp'

    def ready(self):
        import cityApp.signals
