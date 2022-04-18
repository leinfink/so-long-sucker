from django.apps import AppConfig

class GameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'game'
 
    # importing signals so they are available outside of the models
    def ready(self):
        from game import signals
