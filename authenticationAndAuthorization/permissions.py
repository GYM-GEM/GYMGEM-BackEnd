from functools import wraps
from django.http import JsonResponse
from accounts.models import Account

def required_roles(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check authentication first
            if not request.user.is_authenticated:
                return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)
            
            # If no roles specified, just require authentication
            if not allowed_roles:
                return view_func(request, *args, **kwargs)
            
            user = request.user
            account = Account.objects.filter(pk=user.pk).first()
            
            if account:
                user_roles = set(account.profiles.values_list('profile_type', flat=True))
            else:
                user_roles = set()
            
            # Add roles to user for potential use in the view
            user.roles = user_roles
            
            # Check if user has any of the required roles
            if not user_roles.intersection(set(allowed_roles)):
                return JsonResponse({'detail': 'You do not have permission to perform this action.'}, status=403)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

