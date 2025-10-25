from __future__ import annotations
from typing import List, Dict
from itertools import count

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accesscontrol.services import has_permission
import logging
log = logging.getLogger("mockbiz.views")
# Ephemeral in-memory items (id, owner_id, name)
_items: List[Dict] = []
_id_gen = count(1)

def _ensure_seed_for_user(user_id: int):
    # Create a couple of items for a user if none exist
    if not any(it["owner_id"] == user_id for it in _items):
        _items.append({"id": next(_id_gen), "owner_id": user_id, "name": f"Item A (user {user_id})"})
        _items.append({"id": next(_id_gen), "owner_id": user_id, "name": f"Item B (user {user_id})"})

def _get_user_from_request(request):
    """
    Retrieve the authenticated user from either DRF's Request or the
    underlying Django HttpRequest that the JWT middleware set.
    """
    user = getattr(request, "user", None)
    if not user:
        underlying = getattr(request, "_request", None)
        if underlying is not None:
            user = getattr(underlying, "user", None)
    return user

class ItemsView(APIView):
    """
    GET  /api/mock/items/        -> needs read/read_all on element 'items'
    POST /api/mock/items/        -> needs create
    """
    def get(self, request):
        user = _get_user_from_request(request)
        if not (user and getattr(user, "is_authenticated", False)):
            log.info("items.get.unauth")
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        allowed_all = has_permission(user, "items", "read", None)
        if not allowed_all:
            # maybe allowed only for own items?
            allowed_own = has_permission(user, "items", "read", owner_id=user.id)
            if not allowed_own:
                log.info("items.get.forbidden user_id=%s", user.id)
                return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
            _ensure_seed_for_user(user.id)
            mine = [it for it in _items if it["owner_id"] == user.id]
            return Response(mine)

        # read_all
        if not _items:
            # seed a couple of different owners just for demo
            _ensure_seed_for_user(user.id)
        return Response(_items)

    def post(self, request):
        user = _get_user_from_request(request)
        if not (user and getattr(user, "is_authenticated", False)):
            log.info("items.post.unauth")
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        if not has_permission(user, "items", "create", owner_id=user.id):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        name = request.data.get("name") or f"New Item by {user.id}"
        obj = {"id": next(_id_gen), "owner_id": user.id, "name": name}
        _items.append(obj)
        return Response(obj, status=status.HTTP_201_CREATED)

class ItemDetailView(APIView):
    """
    PUT    /api/mock/items/<id>/ -> needs update or update_all
    DELETE /api/mock/items/<id>/ -> needs delete or delete_all
    """
    def _find(self, item_id: int):
        for it in _items:
            if it["id"] == item_id:
                return it
        return None

    def put(self, request, item_id: int):
        user = _get_user_from_request(request)
        if not (user and getattr(user, "is_authenticated", False)):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        it = self._find(int(item_id))
        if not it:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        owner_id = it["owner_id"]
        if not has_permission(user, "items", "update", owner_id=owner_id):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        it["name"] = request.data.get("name") or it["name"]
        return Response(it)

    def delete(self, request, item_id: int):
        user = _get_user_from_request(request)
        if not (user and getattr(user, "is_authenticated", False)):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        it = self._find(int(item_id))
        if not it:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        owner_id = it["owner_id"]
        if not has_permission(user, "items", "delete", owner_id=owner_id):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        _items.remove(it)
        return Response(status=status.HTTP_204_NO_CONTENT)
