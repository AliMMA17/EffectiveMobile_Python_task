from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from .jwt import verify_jwt
import logging
log = logging.getLogger("authn.drf_auth")
User = get_user_model()

class JWTHeaderAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
        if not raw:
            log.debug("no Authorization header")
            return None  # anonymous
        parts = raw.strip().split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        token = parts[1].strip().strip('"').strip("'")
        payload = verify_jwt(token)
        if not payload:
            log.info("access JWT invalid/expired")
            raise AuthenticationFailed("Invalid or expired token")
        sub = payload.get("sub")
        try:
            user = User.objects.get(pk=int(sub))
        except Exception:
            log.info("inactive user id=%s", user.id)
            raise AuthenticationFailed("User not found")
        if not user.is_active:
            raise AuthenticationFailed("User inactive")
        return (user, None)
