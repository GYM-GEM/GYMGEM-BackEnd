from django.apps import AppConfig

class InteractiveSessionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interactive_sessions'

    def ready(self):
        import interactive_sessions.cron  # 🔥 دي اللي كانت ناقصة
