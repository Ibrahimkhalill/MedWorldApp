from django.apps import AppConfig
  

class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'
    
    def ready(self):
        from .scheduler import start_scheduler
        start_scheduler()
  
        
