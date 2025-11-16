from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

     # create ready method
    def ready(self):
        # import signals
        import accounts.signals
