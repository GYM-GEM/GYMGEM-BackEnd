"""
Custom permission classes for role-based access control.
"""
import logging
from typing import Any, List, Type, Union

import jwt
from django.conf import settings
from django.http import HttpRequest
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView

from profiles.models import Profile


logger = logging.getLogger('gymgem.auth')


def HasRole(allowed_roles: Union[str, List[str]]) -> Type[BasePermission]:
    """
    Factory function that returns a permission class for specific roles.
    
    Args:
        allowed_roles: A single role string or list of allowed role strings.
                      Valid roles: 'trainer', 'trainee', 'gym', 'store', 'admin'
    
    Usage:
        permission_classes = [HasRole(['trainer', 'gym'])]
        permission_classes = [HasRole('trainer')]
    
    Returns:
        A permission class that checks if the user has the required role.
    """
    # Normalize to list if string provided
    if isinstance(allowed_roles, str):
        roles_list = [allowed_roles]
    else:
        roles_list = list(allowed_roles)

    class _HasRole(BasePermission):
        """Permission class that checks user roles from JWT token."""
        
        def has_permission(self, request: HttpRequest, view: APIView) -> bool:
            auth_header = request.headers.get("Authorization")
            token = None
            payload = None

            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

            if token:
                try:
                    payload = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=["HS256"]
                    )
                except jwt.ExpiredSignatureError:
                    logger.warning("Permission check failed: expired token")
                    return False
                except jwt.InvalidTokenError as e:
                    logger.warning("Permission check failed: %s", str(e))
                    return False

            user = request.user
            if not user or not user.is_authenticated:
                logger.debug("Permission denied: user not authenticated")
                return False
                
            # Superusers bypass role checks
            if user.is_superuser:
                logger.debug("Permission granted: superuser bypass")
                return True

            if not payload:
                logger.warning("Permission denied: no valid token payload")
                return False

            profile_id = payload.get("current_profile")
            if not profile_id:
                logger.warning(
                    "Permission denied: no current_profile in token for user %s",
                    user.pk
                )
                return False

            try:
                profile = Profile.objects.get(id=profile_id)
                user_role = profile.profile_type
            except Profile.DoesNotExist:
                logger.warning(
                    "Permission denied: profile %s not found",
                    profile_id
                )
                return False

            has_permission = user_role in roles_list
            
            if not has_permission:
                logger.info(
                    "Permission denied: role '%s' not in allowed roles %s for user %s",
                    user_role,
                    roles_list,
                    user.pk
                )
            
            return has_permission

    return _HasRole
