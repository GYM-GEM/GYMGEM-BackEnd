import jwt
from django.conf import settings
from rest_framework.permissions import BasePermission
from profiles.models import Profile


def HasRole(allowed_roles):
    """
    Factory function that returns a permission class for specific roles.
    Usage: permission_classes=[HasRole(['trainer', 'gym'])]
    """

    class _HasRole(BasePermission):
        def has_permission(self, request, view):
            auth_header = request.headers.get("Authorization")
            token = None

            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

            payload = None
            if token:

                try:
                    payload = jwt.decode(
                        token, settings.SECRET_KEY, algorithms=["HS256"]
                    )
                except Exception as e:
                    print("Token decode error:", str(e))

            user = request.user
            if not user or not user.is_authenticated:
                return False
            if user.is_superuser:
                return True  # bypass role checks

            profile = payload.get("current_profile", None)
            user_role = (
                Profile.objects.filter(id=profile).first().profile_type
                if profile
                else None
            )
            print('pl', payload)
            print(profile)
            print(allowed_roles)
            print("print:", user_role)
            return bool(user_role in allowed_roles)

    return _HasRole
