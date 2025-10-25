# authn/middleware.py
from __future__ import annotations
import logging
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from .jwt import verify_jwt, JWT_SECRET, JWT_ALG  # we will log alg/secret length for sanity

logger = logging.getLogger("authn.middleware")
User = get_user_model()

def _clean_token(raw: str) -> str:
    t = raw.strip()
    if t.startswith('"') and t.endswith('"') and len(t) >= 2:
        t = t[1:-1]
    if t.startswith("'") and t.endswith("'") and len(t) >= 2:
        t = t[1:-1]
    return t.strip()

def _user_from_token(token: str):
    payload = verify_jwt(token)
    if not payload:
        return None, None
    sub = payload.get("sub")
    try:
        user = User.objects.get(pk=int(sub))
    except (User.DoesNotExist, ValueError, TypeError):
        return payload, None
    return payload, (user if user.is_active else None)

class JWTAuthMiddleware(MiddlewareMixin):
    """
    - Accepts 'Authorization: Bearer <token>' (scheme is case-insensitive).
    - Ignores missing/invalid headers silently (so admin/session continues to work).
    - Only sets request.user when a valid token is provided.
    """
    def process_request(self, request):
        # Basic request context in logs
        try:
            path = getattr(request, "path", "?")
            method = getattr(request, "method", "?")
        except Exception:
            path = method = "?"
        auth = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")

        if not auth:
            logger.debug("[JWT MW] %s %s -> no Authorization header", method, path)
            return None

        parts = auth.strip().split()
        if len(parts) != 2:
            logger.debug("[JWT MW] %s %s -> malformed Authorization header: %r", method, path, auth)
            return None

        scheme, token_raw = parts[0], _clean_token(parts[1])
        if scheme.lower() != "bearer" or not token_raw:
            logger.debug("[JWT MW] %s %s -> not a Bearer token (scheme=%r)", method, path, scheme)
            return None

        # Token logs (safe: only partial)
        safe_token = f"{token_raw[:12]}...{token_raw[-8:]}" if len(token_raw) > 24 else "<short>"
        logger.info("[JWT MW] %s %s -> bearer token seen: %s (alg=%s, secret_len=%d)",
                    method, path, safe_token, JWT_ALG, len(JWT_SECRET or ""))

        payload, user = _user_from_token(token_raw)
        if payload is None:
            logger.info("[JWT MW] %s %s -> token verification failed", method, path)
            return None

        sub = payload.get("sub")
        logger.info("[JWT MW] %s %s -> token ok; sub=%r", method, path, sub)

        if user is None:
            # exists? active? (best-effort)
            exists = False
            active = None
            try:
                u = User.objects.filter(pk=int(sub)).first()
                if u:
                    exists = True
                    active = u.is_active
            except Exception:
                pass
            logger.warning("[JWT MW] %s %s -> user not resolved (exists=%s, active=%s)",
                           method, path, exists, active)
            return None

        request.user = user
        logger.info("[JWT MW] %s %s -> request.user set to id=%s email=%s",
                    method, path, getattr(user, "id", None), getattr(user, "email", None))
        return None
