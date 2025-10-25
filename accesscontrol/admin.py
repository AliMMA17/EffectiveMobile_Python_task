from django.contrib import admin
from .models import Role, BusinessElement, AccessRule

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    filter_horizontal = ("users",)

@admin.register(BusinessElement)
class BusinessElementAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name")
    search_fields = ("slug", "name")

@admin.register(AccessRule)
class AccessRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id", "role", "element",
        "read_permission", "read_all_permission",
        "create_permission",
        "update_permission", "update_all_permission",
        "delete_permission", "delete_all_permission",
    )
    list_filter = ("role", "element")
