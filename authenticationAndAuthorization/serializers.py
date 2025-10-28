from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth import get_user_model
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


class MyTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        # Validate refresh normally
        refresh = RefreshToken(attrs['refresh'])

        # Rebuild access token from current DB state
        user_id = refresh.get('user_id') or refresh.get('sub')
        user = get_user_model().objects.get(pk=user_id)
        account = getattr(user, 'account', None) or Account.objects.filter(pk=user.pk).first()

        access = AccessToken.for_user(user)
        access['username'] = user.username
        access['email'] = user.email
        access['account_id'] = account.pk if account else None
        access['profile_types'] = list(account.profiles.values_list('profile_type', flat=True)) if account else []

        return {
            'access': str(access),
            'refresh': str(refresh)  # include this only if you want to echo it back
        }
