
from __future__ import annotations
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

class RefreshToken(models.Model):
    """
    Secure server-stored refresh token (rotation-based).
    We store only a SHA-256 hash of the token. The raw token is returned to the client once.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="refresh_tokens"
    )
    token_hash = models.CharField(max_length=128, unique=True)  # hex-encoded sha256 (64), padded
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    replaced_by = models.OneToOneField(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replaces"
    )
    family = models.UUIDField(default=uuid.uuid4, editable=False)
    user_agent = models.CharField(max_length=256, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "family"]),
            models.Index(fields=["expires_at"]),
        ]

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and timezone.now() < self.expires_at

    def __str__(self) -> str:
        status = "active" if self.is_active else "inactive"
        return f"RT({self.user_id}, {self.family}, {status})"