import jwt
from django.conf import settings
from accounts.models import Account
from rest_framework.permissions import BasePermission
from profiles.models import Profile
class IsAuthenticatedAndHasRole(BasePermission):
    """
    DRF permission class to check if user is authenticated and has one of the required roles.
    Set `required_roles` attribute on the view to specify allowed roles.
    If no roles specified, only authentication is required.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        allowed_roles = getattr(view, 'required_roles', [])
        if user.is_superuser:
            return True  # superusers bypass everything
        if not allowed_roles:
            return True  # Only authentication required

        account = Account.objects.filter(pk=getattr(user, 'pk', None)).first()
        if account:
            user_roles = set(account.profiles.values_list('profile_type', flat=True))
        else:
            user_roles = set(user.groups.values_list('name', flat=True))

        try:
            user.roles = user_roles
        except Exception:
            pass

        return bool(user_roles.intersection(set(allowed_roles)))


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
                        token,
                        settings.SECRET_KEY,
                        algorithms=["HS256"]
                    )
                except Exception as e:
                    print("Token decode error:", str(e))

            user = request.user
            if not user or not user.is_authenticated:
                return False
            if user.is_superuser:
                return True  # bypass role checks
            
            profile = payload.get("current_profile", None)
            user_role = Profile.objects.filter(id=profile).first().profile_type if profile else None

            return bool(user_role in allowed_roles)
    
    return _HasRole