"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

import supplychain.views as views


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    # Auth (JWT)
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/me/", views.MeView.as_view(), name="me"),
    # User management
    path("api/users/", views.UserListCreateView.as_view(), name="user-list-create"),
    path(
        "api/users/<int:pk>/", views.UserDetailUpdateView.as_view(), name="user-detail"
    ),
    path(
        "api/users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user-delete"
    ),
    # Product management
    path(
        "api/products/",
        views.ProductListCreateView.as_view(),
        name="product-list-create",
    ),
    path(
        "api/products/<int:pk>/",
        views.ProductDetailUpdateView.as_view(),
        name="product-detail",
    ),
    path(
        "api/products/<int:pk>/delete/",
        views.ProductDeleteView.as_view(),
        name="product-delete",
    ),
    # Batch management
    path("api/batches/", views.BatchListCreateView.as_view(), name="batch-list-create"),
    path(
        "api/batches/<int:pk>/",
        views.BatchDetailUpdateView.as_view(),
        name="batch-detail",
    ),
    path(
        "api/batches/<int:pk>/delete/",
        views.BatchDeleteView.as_view(),
        name="batch-delete",
    ),
    # Pack management
    path("api/packs/", views.PackListCreateView.as_view(), name="pack-list-create"),
    path(
        "api/packs/<int:pk>/", views.PackDetailUpdateView.as_view(), name="pack-detail"
    ),
    path(
        "api/packs/<int:pk>/delete/", views.PackDeleteView.as_view(), name="pack-delete"
    ),
    # Shipment management
    path(
        "api/shipments/",
        views.ShipmentListCreateView.as_view(),
        name="shipment-list-create",
    ),
    path(
        "api/shipments/<int:pk>/",
        views.ShipmentDetailUpdateView.as_view(),
        name="shipment-detail",
    ),
    path(
        "api/shipments/<int:pk>/delete/",
        views.ShipmentDeleteView.as_view(),
        name="shipment-delete",
    ),
    # Event management
    path("api/events/", views.EventListCreateView.as_view(), name="event-list-create"),
    path(
        "api/events/<int:pk>/",
        views.EventDetailUpdateView.as_view(),
        name="event-detail",
    ),
    path(
        "api/events/<int:pk>/delete/",
        views.EventDeleteView.as_view(),
        name="event-delete",
    ),
]
