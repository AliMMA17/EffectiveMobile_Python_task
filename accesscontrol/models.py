from __future__ import annotations
from django.conf import settings
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=64, unique=True)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="roles", blank=True
    )

    def __str__(self) -> str:
        return self.name


class BusinessElement(models.Model):
    slug = models.SlugField(max_length=64, unique=True)  # e.g., "users", "items"
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.slug


class AccessRule(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="rules")
    element = models.ForeignKey(BusinessElement, on_delete=models.CASCADE, related_name="rules")

    read_permission = models.BooleanField(default=False)
    read_all_permission = models.BooleanField(default=False)
    create_permission = models.BooleanField(default=False)
    update_permission = models.BooleanField(default=False)
    update_all_permission = models.BooleanField(default=False)
    delete_permission = models.BooleanField(default=False)
    delete_all_permission = models.BooleanField(default=False)

    class Meta:
        unique_together = (("role", "element"),)

    def __str__(self) -> str:
        return f"{self.role}:{self.element}"
