from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
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
            return {
                "detail": "Account not found"
            }  # fallback: return token without extra claims
        # Add custom claims
        token["account_id"] = account.pk
        token["current_profile"] = (
            account.default_profile.id if account and account.default_profile else None
        )
        return token


class MyTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, headers):
        refresh_token = headers.get("refresh")
        if not refresh_token:
            raise serializers.ValidationError({"detail": "refresh token is required"})
        try:
            refresh = RefreshToken(refresh_token)
        except Exception:
            raise serializers.ValidationError(
                {"detail": "Invalid or blacklisted token"}
            )

        # Rebuild access token from current DB state
        user_id = refresh.get("user_id") or refresh.get("sub")
        user = get_user_model().objects.get(pk=user_id)
        account = Account.objects.filter(pk=user.pk).first()

        access = AccessToken.for_user(user)
        access["account_id"] = account.pk
        access["current_profile"] = refresh.get("current_profile", None)
        return {
            "access": str(access),
            "refresh": str(refresh),  # include this only if you want to echo it back
        }


class RotateRefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, data):
        refresh_token = data.get("refresh")

        if not refresh_token:
            raise serializers.ValidationError({"detail": "refresh token is required"})

        # Validate old refresh token
        try:
            old_refresh = RefreshToken(refresh_token)
        except Exception:
            raise serializers.ValidationError(
                {"detail": "Invalid or blacklisted token"}
            )

        user_id = old_refresh.get("user_id") or old_refresh.get("sub")
        User = get_user_model()
        user = User.objects.get(pk=user_id)

        # Blacklist old refresh token
        old_refresh.blacklist()

        # Create new pair
        new_refresh = RefreshToken.for_user(user)
        account = Account.objects.filter(pk=user.pk).first()

        access = new_refresh.access_token
        access["username"] = user.username
        access["email"] = user.email
        # access['current_profile'] = user.
        access["account_id"] = account.pk if account else None
        access["profile_types"] = (
            list(account.profiles.values_list("profile_type", flat=True))
            if account
            else []
        )

        return {
            "refresh": str(new_refresh),
            "access": str(access),
        }
