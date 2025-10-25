from django.urls import path
from .views import ItemsView, ItemDetailView

urlpatterns = [
    path("items/", ItemsView.as_view(), name="mock-items"),
    path("items/<int:item_id>/", ItemDetailView.as_view(), name="mock-item-detail"),
]
