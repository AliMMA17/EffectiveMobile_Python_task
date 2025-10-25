from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoleViewSet, BusinessElementViewSet, AccessRuleViewSet

router = DefaultRouter()
router.register("roles", RoleViewSet)
router.register("elements", BusinessElementViewSet)
router.register("rules", AccessRuleViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
