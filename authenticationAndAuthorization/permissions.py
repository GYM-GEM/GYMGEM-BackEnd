from accounts.models import Account
from rest_framework.permissions import BasePermission

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
            user = request.user
            if not user or not user.is_authenticated:
                return False

            account = Account.objects.filter(pk=getattr(user, 'pk', None)).first()
            if account:
                user_roles = set(account.profiles.values_list('profile_type', flat=True))
            else:
                user_roles = set(user.groups.values_list('name', flat=True))
            
            roles = allowed_roles if isinstance(allowed_roles, list) else [allowed_roles]
            return bool(user_roles.intersection(set(roles)))
    
    return _HasRole