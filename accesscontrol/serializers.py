from __future__ import annotations
from rest_framework import serializers
from .models import Role, BusinessElement, AccessRule

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name", "users")

class BusinessElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessElement
        fields = ("id", "slug", "name", "description")

class AccessRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRule
        fields = (
            "id", "role", "element",
            "read_permission", "read_all_permission",
            "create_permission",
            "update_permission", "update_all_permission",
            "delete_permission", "delete_all_permission",
        )
