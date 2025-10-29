from functools import wraps
from django.http import JsonResponse
from accounts.models import Account

def required_roles(*allowed_roles):
    if not allowed_roles:
        return False
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            account = Account.objects.filter(pk=user.pk).first()
            if not user.is_authenticated:
                return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)
            if not user.roles.intersection(set(allowed_roles)):
               return JsonResponse({'detail': 'You do not have permission to perform this action.'}, status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

