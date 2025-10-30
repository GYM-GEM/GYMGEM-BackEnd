from functools import wraps
from django.http import JsonResponse
from accounts.models import Account

def required_roles(*allowed_roles):
    """
    Flexible decorator compatible with:
      - class-based views: @required_roles('admin') sets view.required_roles = [...]
      - function-based views: @required_roles('admin') wraps the function and enforces roles
    If no roles provided (empty call) the wrapper will only require authentication.
    """
    def decorator(obj):
        # If decorator was applied to a class, set attribute and return class unchanged
        if isinstance(obj, type):
            setattr(obj, 'required_roles', list(allowed_roles))
            return obj

        # Otherwise treat obj as a function (function-based view)
        @wraps(obj)
        def _wrapped_view(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated:
                return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)

            # If no roles specified, only require authentication
            if not allowed_roles:
                return obj(request, *args, **kwargs)

            # Try to get roles from Account.profiles.profile_type (your existing model)
            account = Account.objects.filter(pk=getattr(user, 'pk', None)).first()
            if account:
                user_roles = set(account.profiles.values_list('profile_type', flat=True))
            else:
                # Fallback to Django groups if no Account or profiles
                user_roles = set(user.groups.values_list('name', flat=True))

            # attach roles to user for potential use in view
            try:
                user.roles = user_roles
            except Exception:
                pass

            if not user_roles.intersection(set(allowed_roles)):
                return JsonResponse({'detail': 'You do not have permission to perform this action.'}, status=403)

            return obj(request, *args, **kwargs)
        return _wrapped_view
    return decorator

