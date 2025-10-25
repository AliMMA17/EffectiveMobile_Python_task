from __future__ import annotations
from typing import Optional
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import AccessRule

User = get_user_model()

# action in {"read","create","update","delete"}
def has_permission(user: Optional[User], element_slug: str, action: str, owner_id: Optional[int] = None) -> bool:
    if not user or not getattr(user, "is_active", False):
        return False
    if getattr(user, "is_superuser", False):
        return True

    # aggregate rules across user roles
    qs = AccessRule.objects.filter(
        role__in=user.roles.all(),
        element__slug=element_slug,
    ).distinct()

    if not qs.exists():
        return False

    # any role that grants is enough
    for rule in qs:
        if action == "read":
            if rule.read_all_permission:
                return True
            if rule.read_permission and owner_id and int(owner_id) == int(user.id):
                return True
        elif action == "create":
            if rule.create_permission:
                return True
        elif action == "update":
            if rule.update_all_permission:
                return True
            if rule.update_permission and owner_id and int(owner_id) == int(user.id):
                return True
        elif action == "delete":
            if rule.delete_all_permission:
                return True
            if rule.delete_permission and owner_id and int(owner_id) == int(user.id):
                return True
    return False
