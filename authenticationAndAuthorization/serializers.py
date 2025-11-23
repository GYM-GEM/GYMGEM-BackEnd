from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth import get_user_model
from accounts.models import Account

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Resolve Account from the authenticated user (Account extends User via multi-table inheritance)
        try:
            account = Account.objects.get(pk=user.pk)
        except Account.DoesNotExist:
            return ({'detail': 'Account not found'})  # fallback: return token without extra claims
        # Add custom claims
        token['account_id'] = account.pk
        token['current_profile'] = account.default_profile.id if account and account.default_profile else None
        return token


class MyTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, headers):
        refresh_token = headers.get('refresh')
        if not refresh_token:
            raise serializers.ValidationError({'detail': 'refresh token is required'})
        try:
            refresh = RefreshToken(refresh_token)
        except Exception:
            raise serializers.ValidationError({'detail': 'Invalid or blacklisted token'})

        # Rebuild access token from current DB state
        user_id = refresh.get('user_id') or refresh.get('sub')
        user = get_user_model().objects.get(pk=user_id)
        account = Account.objects.filter(pk=user.pk).first()

        access = AccessToken.for_user(user)
        access['account_id'] = account.pk 
        access['current_profile'] = refresh.get('current_profile', None)
        return {
            'access': str(access),
            'refresh': str(refresh)  # include this only if you want to echo it back
        }
