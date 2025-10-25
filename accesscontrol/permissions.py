from __future__ import annotations
from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    """
    Admin if:
    - is_superuser OR
    - has role with name 'admin'
    """
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not u:
            return False
        if getattr(u, "is_superuser", False):
            return True
        # hasattr guard for anonymous None
        roles = getattr(u, "roles", None)
        return bool(roles and roles.filter(name__iexact="admin").exists())
