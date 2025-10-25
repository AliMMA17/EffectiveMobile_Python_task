from __future__ import annotations
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from accesscontrol.models import Role, BusinessElement, AccessRule

User = get_user_model()

class Command(BaseCommand):
    help = "Seed demo roles/elements/rules and two users."

    def handle(self, *args, **options):
        # Roles
        admin_role, _ = Role.objects.get_or_create(name="admin")
        manager_role, _ = Role.objects.get_or_create(name="manager")
        user_role, _ = Role.objects.get_or_create(name="user")
        guest_role, _ = Role.objects.get_or_create(name="guest")

        # Elements
        items, _ = BusinessElement.objects.get_or_create(slug="items", defaults={"name": "Items"})
        users_el, _ = BusinessElement.objects.get_or_create(slug="users", defaults={"name": "Users"})
        orders, _ = BusinessElement.objects.get_or_create(slug="orders", defaults={"name": "Orders"})
        rules_el, _ = BusinessElement.objects.get_or_create(slug="rules", defaults={"name": "Access Rules"})

        # Admin: everything
        AccessRule.objects.get_or_create(
            role=admin_role, element=items,
            defaults=dict(read_permission=True, read_all_permission=True,
                          create_permission=True,
                          update_permission=True, update_all_permission=True,
                          delete_permission=True, delete_all_permission=True)
        )
        AccessRule.objects.get_or_create(
            role=admin_role, element=users_el,
            defaults=dict(read_permission=True, read_all_permission=True,
                          create_permission=True,
                          update_permission=True, update_all_permission=True,
                          delete_permission=True, delete_all_permission=True)
        )
        AccessRule.objects.get_or_create(
            role=admin_role, element=orders,
            defaults=dict(read_permission=True, read_all_permission=True,
                          create_permission=True,
                          update_permission=True, update_all_permission=True,
                          delete_permission=True, delete_all_permission=True)
        )
        AccessRule.objects.get_or_create(
            role=admin_role, element=rules_el,
            defaults=dict(read_permission=True, read_all_permission=True,
                          create_permission=True,
                          update_permission=True, update_all_permission=True,
                          delete_permission=True, delete_all_permission=True)
        )

        # Manager: read_all items/orders, update_all items
        AccessRule.objects.get_or_create(
            role=manager_role, element=items,
            defaults=dict(read_all_permission=True, update_all_permission=True, create_permission=True)
        )
        AccessRule.objects.get_or_create(
            role=manager_role, element=orders,
            defaults=dict(read_all_permission=True)
        )

        # User: own items (CRUD on own), read own users
        AccessRule.objects.get_or_create(
            role=user_role, element=items,
            defaults=dict(read_permission=True, create_permission=True, update_permission=True, delete_permission=True)
        )
        AccessRule.objects.get_or_create(
            role=user_role, element=users_el,
            defaults=dict(read_permission=True)
        )

        # Users
        admin, created = User.objects.get_or_create(email="admin@example.com", defaults={"first_name": "Admin"})
        if created:
            admin.set_password("Passw0rd!")
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
        admin_role.users.add(admin)

        bob, created = User.objects.get_or_create(email="bob@example.com", defaults={"first_name": "Bob"})
        if created:
            bob.set_password("Passw0rd!")
            bob.save()
        user_role.users.add(bob)

        self.stdout.write(self.style.SUCCESS("Seeded demo data."))
