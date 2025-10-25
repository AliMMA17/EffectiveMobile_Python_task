from __future__ import annotations
import os
import uuid
import secrets
import hashlib
from datetime import timedelta
from typing import Optional, Tuple
from django.utils import timezone
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from .models import RefreshToken

User = get_user_model()

REFRESH_TOKEN_BYTES = int(os.getenv("REFRESH_TOKEN_BYTES", "32"))  # ~256 bits
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "14"))

def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _client_context(request: Optional[HttpRequest]) -> tuple[str, Optional[str]]:
    if not request:
        return "", None
    ua = request.META.get("HTTP_USER_AGENT", "")[:256]
    ip = request.META.get("REMOTE_ADDR")
    return ua, ip

def issue_refresh_token(user: User, request: Optional[HttpRequest] = None, family: Optional[uuid.UUID] = None) -> Tuple[str, RefreshToken]:
    raw = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    token_hash = _hash_token(raw)
    expires_at = timezone.now() + timedelta(days=REFRESH_TOKEN_DAYS)
    ua, ip = _client_context(request)
    rt = RefreshToken.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=expires_at,
        family=family or uuid.uuid4(),
        user_agent=ua,
        ip=ip,
    )
    return raw, rt

def get_refresh_row(raw_token: str) -> Optional[RefreshToken]:
    if not raw_token:
        return None
    token_hash = _hash_token(raw_token)
    return RefreshToken.objects.filter(token_hash=token_hash).first()

def revoke_refresh(rt: RefreshToken) -> None:
    if rt.revoked_at is None:
        rt.revoked_at = timezone.now()
        rt.save(update_fields=["revoked_at"])

def rotate_refresh(rt: RefreshToken, request: Optional[HttpRequest] = None) -> Tuple[str, RefreshToken]:
    # revoke current
    revoke_refresh(rt)
    # issue replacement in same family
    new_raw, new_rt = issue_refresh_token(rt.user, request=request, family=rt.family)
    rt.replaced_by = new_rt
    rt.save(update_fields=["replaced_by"])
    return new_raw, new_rt