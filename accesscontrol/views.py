from __future__ import annotations
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Role, BusinessElement, AccessRule
from .serializers import RoleSerializer, BusinessElementSerializer, AccessRuleSerializer
from .permissions import IsAdminRole

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by("id")
    serializer_class = RoleSerializer
    permission_classes = [IsAdminRole]

class BusinessElementViewSet(viewsets.ModelViewSet):
    queryset = BusinessElement.objects.all().order_by("id")
    serializer_class = BusinessElementSerializer
    permission_classes = [IsAdminRole]

class AccessRuleViewSet(viewsets.ModelViewSet):
    queryset = AccessRule.objects.select_related("role", "element").all().order_by("id")
    serializer_class = AccessRuleSerializer
    permission_classes = [IsAdminRole]
