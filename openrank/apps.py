from django.apps import AppConfig

class OpenrankConfig(AppConfig):
    name = 'openrank'

    def ready(self):
        import openrank.signals
