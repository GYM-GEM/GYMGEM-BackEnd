from rest_framework import permissions

class AllowSuperuserBypass(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_superuser:
            return True
        return permissions.IsAuthenticated().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_superuser:
            return True
        return permissions.IsAuthenticated().has_object_permission(request, view, obj)