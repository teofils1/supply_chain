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
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
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
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
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
    # Blockchain integrity endpoints
    path(
        "api/events/<int:pk>/anchor/",
        views.EventBlockchainAnchorView.as_view(),
        name="event-blockchain-anchor",
    ),
    path(
        "api/events/<int:pk>/verify/",
        views.EventBlockchainVerifyView.as_view(),
        name="event-blockchain-verify",
    ),
    path(
        "api/events/<int:pk>/integrity/",
        views.EventIntegrityVerifyView.as_view(),
        name="event-integrity-verify",
    ),
    # Analytics endpoints
    path(
        "api/analytics/summary/",
        views.AnalyticsSummaryView.as_view(),
        name="analytics-summary",
    ),
    path(
        "api/analytics/kpis/",
        views.SupplyChainKPIsView.as_view(),
        name="analytics-kpis",
    ),
    path(
        "api/analytics/batch-yield/",
        views.BatchYieldAnalysisView.as_view(),
        name="analytics-batch-yield",
    ),
    path(
        "api/analytics/carrier-performance/",
        views.CarrierPerformanceView.as_view(),
        name="analytics-carrier-performance",
    ),
    path(
        "api/analytics/temperature-excursions/",
        views.TemperatureExcursionTrendsView.as_view(),
        name="analytics-temperature-excursions",
    ),
    # Document management
    path(
        "api/documents/",
        views.DocumentListCreateView.as_view(),
        name="document-list-create",
    ),
    path(
        "api/documents/<int:pk>/",
        views.DocumentDetailView.as_view(),
        name="document-detail",
    ),
    path(
        "api/documents/<int:pk>/delete/",
        views.DocumentDeleteView.as_view(),
        name="document-delete",
    ),
    path(
        "api/documents/<int:pk>/download/",
        views.DocumentDownloadView.as_view(),
        name="document-download",
    ),
    path(
        "api/documents/<int:pk>/new-version/",
        views.DocumentNewVersionView.as_view(),
        name="document-new-version",
    ),
    path(
        "api/<str:entity_type>/<int:entity_id>/documents/",
        views.EntityDocumentsView.as_view(),
        name="entity-documents",
    ),
    # PDF generation endpoints
    path(
        "api/shipments/<int:pk>/generate-label/",
        views.ShipmentGenerateLabelView.as_view(),
        name="shipment-generate-label",
    ),
    path(
        "api/shipments/<int:pk>/generate-packing-list/",
        views.ShipmentGeneratePackingListView.as_view(),
        name="shipment-generate-packing-list",
    ),
    path(
        "api/batches/<int:pk>/generate-coa/",
        views.BatchGenerateCoaView.as_view(),
        name="batch-generate-coa",
    ),
    # Notification management
    path(
        "api/notifications/rules/",
        views.NotificationRuleListCreateView.as_view(),
        name="notification-rule-list-create",
    ),
    path(
        "api/notifications/rules/<int:pk>/",
        views.NotificationRuleDetailView.as_view(),
        name="notification-rule-detail",
    ),
    path(
        "api/notifications/rules/<int:pk>/toggle/",
        views.NotificationRuleToggleView.as_view(),
        name="notification-rule-toggle",
    ),
    path(
        "api/notifications/logs/",
        views.NotificationLogListView.as_view(),
        name="notification-log-list",
    ),
    path(
        "api/notifications/logs/<int:pk>/",
        views.NotificationLogDetailView.as_view(),
        name="notification-log-detail",
    ),
    path(
        "api/notifications/logs/<int:pk>/acknowledge/",
        views.NotificationLogAcknowledgeView.as_view(),
        name="notification-log-acknowledge",
    ),
    path(
        "api/notifications/logs/acknowledge-all/",
        views.NotificationLogAcknowledgeAllView.as_view(),
        name="notification-log-acknowledge-all",
    ),
    path(
        "api/notifications/logs/unread-count/",
        views.NotificationLogUnreadCountView.as_view(),
        name="notification-log-unread-count",
    ),
    path(
        "api/notifications/logs/recent/",
        views.NotificationLogRecentView.as_view(),
        name="notification-log-recent",
    ),
]
