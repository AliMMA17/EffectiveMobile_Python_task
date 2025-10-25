from __future__ import annotations
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from authn.jwt import verify_jwt_verbose
from authn.jwt import make_jwt
from .serializers import RegisterSerializer, LoginSerializer, UserMeSerializer
from authn.services import issue_refresh_token, get_refresh_row, rotate_refresh, revoke_refresh
User = get_user_model()


class RegisterView(APIView):
    authentication_classes = []  # handled by middleware
    permission_classes = []

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
        user = s.save()
        return Response({"id": user.id, "email": user.email}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        s = LoginSerializer(data=request.data)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
        user = s.validated_data["user"]
        token = make_jwt(user.id)
        # Stateless: client stores token (e.g., Authorization header).
        return Response({"token": token, "user": UserMeSerializer(user).data})


class LogoutView(APIView):
    """Stateless logout; client forgets token."""
    def post(self, request):
        return Response({"detail": "Logged out (stateless)."}, status=status.HTTP_200_OK)


class MeView(APIView):
    def _get_user(self, request) -> User | None:
        # DRF request.user is None with your settings; fall back to underlying Django request
        user = getattr(request, "user", None)
        if not user:
            underlying = getattr(request, "_request", None)
            if underlying is not None:
                user = getattr(underlying, "user", None)
        return user

    def _ensure_auth(self, request):
        u = self._get_user(request)
        if not (u and getattr(u, "is_authenticated", False)):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        # make available to downstream code
        request.user = u
        return None

    def get(self, request):
        unauth = self._ensure_auth(request)
        if unauth: return unauth
        return Response(UserMeSerializer(request.user).data)

    def patch(self, request):
        unauth = self._ensure_auth(request)
        if unauth: return unauth
        s = UserMeSerializer(instance=request.user, data=request.data, partial=True)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
        s.save()
        return Response(s.data)

    def delete(self, request):
        unauth = self._ensure_auth(request)
        if unauth: return unauth
        request.user.is_active = False
        request.user.save(update_fields=["is_active"])
        return Response({"detail": "Account deactivated."})

class DebugAuthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        raw = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION", "")
        token = ""
        if raw:
            parts = raw.strip().split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1].strip().strip('"').strip("'")
        return Response({
            "authorization_raw": raw,
            "verify": verify_jwt_verbose(token),
            "user_resolved": getattr(request, "user", None) and getattr(request.user, "id", None),
        })
    


class RefreshView(APIView):
    """
    Exchange a valid refresh token for a NEW access token and a ROTATED refresh token.
    - Accepts: {"refresh": "<raw_refresh_token>"}
    - Returns: {"access": "<jwt>", "refresh": "<new_raw_refresh_token>"}
    """
    authentication_classes = []  # uses refresh token only
    permission_classes = []

    def post(self, request):
        refresh_raw = str(request.data.get("refresh") or "").strip()
        if not refresh_raw:
            return Response({"detail": "refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

        rt = get_refresh_row(refresh_raw)
        if not rt:
            return Response({"detail": "invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        if not rt.is_active:
            return Response({"detail": "refresh token expired or revoked"}, status=status.HTTP_401_UNAUTHORIZED)

        # Rotate refresh token
        new_refresh_raw, _ = rotate_refresh(rt, request=request)

        # Issue new short-lived access
        access = make_jwt(rt.user.id)

        return Response({"access": access, "refresh": new_refresh_raw}, status=status.HTTP_200_OK)