from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from accounts.models import Account

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Resolve Account from the authenticated user (Account extends User via multi-table inheritance)
        account = Account.objects.filter(pk=user.pk).first()

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        if account is not None:
            token['account_id'] = account.pk
            token['profile_types'] = list(account.profiles.values_list('profile_type', flat=True))
        else:
            token['account_id'] = None
            token['profile_types'] = []

        return token
