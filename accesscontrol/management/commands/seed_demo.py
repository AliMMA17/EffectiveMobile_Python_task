from __future__ import annotations
from typing import Dict, Any, Iterable, List, Tuple
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from accesscontrol.models import Role, BusinessElement, AccessRule

User = get_user_model()

ROLES: Iterable[str] = (
    "admin",
    "manager",
    "user",
    "guest",
)

# slug -> {name, description}
ELEMENTS: Dict[str, Dict[str, Any]] = {
    "items":  {"name": "Items",        "description": "Mock items element"},
    "users":  {"name": "Users",        "description": "User accounts"},
    "orders": {"name": "Orders",       "description": "Fictional orders"},
    "rules":  {"name": "Access Rules", "description": "Access control management"},
}

RULES: Dict[str, Dict[str, Dict[str, bool]]] = {
    "admin": {
        "items":  dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        "users":  dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        "orders": dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        "rules":  dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
    },
    "manager": {
        "items":  dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=False),
        "orders": dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=False),
        "users":  dict(read=True, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
        "rules":  dict(read=True, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
    },
    "user": {
        "items":  dict(read=True, read_all=False, create=True, update=True, update_all=False, delete=True, delete_all=False),
        "orders": dict(read=True, read_all=False, create=True, update=True, update_all=False, delete=False, delete_all=False),
        "users":  dict(read=True, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
    },
    "guest": {
        "items":  dict(read=True, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
    },
}

DEMO_USERS: List[Tuple[str, str, str, List[str]]] = [
    ("admin@example.com",   "Passw0rd!", "Admin",   ["admin"]),
    ("manager@example.com", "Passw0rd!", "Manager", ["manager"]),
    ("alice@example.com",   "Passw0rd!", "Alice",   ["user"]),
    ("guest@example.com",   "Passw0rd!", "Guest",   ["guest"]),
]


def ensure_role(name: str) -> Role:
    r, _ = Role.objects.get_or_create(name=name)
    return r


def ensure_element(slug: str, *, name: str, description: str = "") -> BusinessElement:
    e, created = BusinessElement.objects.get_or_create(
        slug=slug,
        defaults={"name": name, "description": description},
    )
    if not created:
        dirty = False
        if e.name != name:
            e.name = name; dirty = True
        if description and e.description != description:
            e.description = description; dirty = True
        if dirty:
            e.save(update_fields=["name", "description"])
    return e


def ensure_rule(role: Role, element: BusinessElement, flags: Dict[str, bool]) -> AccessRule:
    defaults = {
        "read_permission": flags.get("read", False),
        "read_all_permission": flags.get("read_all", False),
        "create_permission": flags.get("create", False),
        "update_permission": flags.get("update", False),
        "update_all_permission": flags.get("update_all", False),
        "delete_permission": flags.get("delete", False),
        "delete_all_permission": flags.get("delete_all", False),
    }
    ar, _ = AccessRule.objects.update_or_create(role=role, element=element, defaults=defaults)
    return ar


def ensure_user(email: str, password: str, first_name: str) -> User:
    u = User.objects.filter(email=email).first()
    if u:
        if not u.is_active:
            u.is_active = True
            u.save(update_fields=["is_active"])
        if first_name and u.first_name != first_name:
            u.first_name = first_name
            u.save(update_fields=["first_name"])
        return u
    u = User.objects.create_user(email=email, password=password, first_name=first_name)
    return u


class Command(BaseCommand):
    help = "Seed roles/elements/rules (idempotent). Optional demo users and mock items."

    def add_arguments(self, parser):
        parser.add_argument("--with-users", action="store_true", help="Create demo users and assign roles.")
        parser.add_argument("--with-items", action="store_true", help="Create mock items for each user (if supported).")
        parser.add_argument("--admin-email", default=None, help="Ensure a superuser with this email.")
        parser.add_argument("--admin-password", default=None, help="Password for the ensured superuser (non-interactive).")

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding RBAC…"))

        # Roles
        role_map = {name: ensure_role(name) for name in ROLES}
        self.stdout.write(self.style.SUCCESS(f"Roles ensured: {', '.join(role_map.keys())}"))

        # Elements
        element_map: Dict[str, BusinessElement] = {}
        for slug, meta in ELEMENTS.items():
            element_map[slug] = ensure_element(slug, name=meta.get("name", slug), description=meta.get("description", ""))
        self.stdout.write(self.style.SUCCESS(f"Elements ensured: {', '.join(element_map.keys())}"))

        # Rules
        for role_name, per_element in RULES.items():
            role = role_map.get(role_name)
            if not role:
                self.stdout.write(self.style.WARNING(f"Role '{role_name}' not configured; skipping."))
                continue
            for slug, flags in per_element.items():
                el = element_map.get(slug)
                if not el:
                    self.stdout.write(self.style.WARNING(f"Element '{slug}' not configured; skipping rule."))
                    continue
                ensure_rule(role, el, flags)
        self.stdout.write(self.style.SUCCESS("Rules upserted."))

        # Ensure superuser if requested
        admin_email = options.get("admin_email")
        admin_password = options.get("admin_password")
        if admin_email:
            su = User.objects.filter(email=admin_email).first()
            if not su:
                if not admin_password:
                    raise SystemExit("--admin-password is required when using --admin-email")
                su = User.objects.create_superuser(email=admin_email, password=admin_password, first_name="Admin")
                self.stdout.write(self.style.SUCCESS(f"Superuser created: {admin_email}"))
            else:
                changed = False
                if not su.is_superuser:
                    su.is_superuser = True; changed = True
                if not su.is_staff:
                    su.is_staff = True; changed = True
                if changed:
                    su.save(update_fields=["is_superuser", "is_staff"])
                self.stdout.write(self.style.SUCCESS(f"Superuser ensured: {admin_email}"))

        # Demo users & roles
        if options.get("with_users"):
            for email, pwd, first_name, role_names in DEMO_USERS:
                u = ensure_user(email, pwd, first_name)
                # Attach roles via Role.users M2M (keeps your current relation style)
                for rn in role_names:
                    r = role_map.get(rn)
                    if r and not r.users.filter(pk=u.pk).exists():
                        r.users.add(u)
                self.stdout.write(self.style.SUCCESS(f"User ensured: {email} [{', '.join(role_names)}]"))

        # Mock items (optional)
        if options.get("with_items"):
            try:
                # Reuse your in-memory seeder if present
                from mockbiz.views import _ensure_seed_for_user
                count = 0
                for u in User.objects.all():
                    _ensure_seed_for_user(u.id)
                    count += 1
                self.stdout.write(self.style.SUCCESS(f"Mock items seeded for {count} users."))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Mock items seeding skipped: {e}"))

        self.stdout.write(self.style.SUCCESS("Seed complete."))
