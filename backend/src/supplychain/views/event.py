from __future__ import annotations

from datetime import datetime
from django.db.models import Q, Prefetch
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .. import models as m
from .. import permissions as p
from .. import serializers as s


class EventListCreateView(generics.ListCreateAPIView):
    """List all events or create a new event."""

    queryset = m.Event.objects.select_related("user", "content_type").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return s.EventCreateSerializer
        return s.EventListSerializer

    def get_queryset(self):
        """Filter events based on query parameters."""
        queryset = super().get_queryset()

        # Search functionality
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search)
                | Q(location__icontains=search)
                | Q(metadata__icontains=search)
                | Q(user__username__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            ).distinct()

        # Filter by event type
        event_type = self.request.query_params.get("event_type", None)
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Filter by entity type
        entity_type = self.request.query_params.get("entity_type", None)
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        # Filter by entity ID
        entity_id = self.request.query_params.get("entity_id", None)
        if entity_id:
            try:
                queryset = queryset.filter(entity_id=int(entity_id))
            except (ValueError, TypeError):
                pass

        # Filter by severity
        severity = self.request.query_params.get("severity", None)
        if severity:
            queryset = queryset.filter(severity=severity)

        # Filter by user
        user_id = self.request.query_params.get("user", None)
        if user_id:
            try:
                queryset = queryset.filter(user_id=int(user_id))
            except (ValueError, TypeError):
                pass

        # Filter by location
        location = self.request.query_params.get("location", None)
        if location:
            queryset = queryset.filter(location__icontains=location)

        # Filter by timestamp range
        timestamp_from = self.request.query_params.get("timestamp_from", None)
        timestamp_to = self.request.query_params.get("timestamp_to", None)

        if timestamp_from:
            try:
                from_date = datetime.fromisoformat(
                    timestamp_from.replace("Z", "+00:00")
                )
                queryset = queryset.filter(timestamp__gte=from_date)
            except ValueError:
                try:
                    # Try date-only format
                    from_date = datetime.strptime(timestamp_from, "%Y-%m-%d")
                    queryset = queryset.filter(timestamp__date__gte=from_date.date())
                except ValueError:
                    pass

        if timestamp_to:
            try:
                to_date = datetime.fromisoformat(timestamp_to.replace("Z", "+00:00"))
                queryset = queryset.filter(timestamp__lte=to_date)
            except ValueError:
                try:
                    # Try date-only format
                    to_date = datetime.strptime(timestamp_to, "%Y-%m-%d")
                    queryset = queryset.filter(timestamp__date__lte=to_date.date())
                except ValueError:
                    pass

        # Filter by date range (alternative date filtering)
        date_from = self.request.query_params.get("date_from", None)
        date_to = self.request.query_params.get("date_to", None)

        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
                queryset = queryset.filter(timestamp__date__gte=from_date)
            except ValueError:
                pass

        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
                queryset = queryset.filter(timestamp__date__lte=to_date)
            except ValueError:
                pass

        # Filter by specific product (through entity relationships)
        product_id = self.request.query_params.get("product", None)
        if product_id:
            try:
                product_id = int(product_id)
                queryset = queryset.filter(
                    Q(entity_type="product", entity_id=product_id)
                    | Q(
                        entity_type="batch",
                        entity_id__in=m.Batch.objects.filter(
                            product_id=product_id
                        ).values_list("id", flat=True),
                    )
                    | Q(
                        entity_type="pack",
                        entity_id__in=m.Pack.objects.filter(
                            batch__product_id=product_id
                        ).values_list("id", flat=True),
                    )
                )
            except (ValueError, TypeError):
                pass

        # Filter by specific batch (through entity relationships)
        batch_id = self.request.query_params.get("batch", None)
        if batch_id:
            try:
                batch_id = int(batch_id)
                queryset = queryset.filter(
                    Q(entity_type="batch", entity_id=batch_id)
                    | Q(
                        entity_type="pack",
                        entity_id__in=m.Pack.objects.filter(
                            batch_id=batch_id
                        ).values_list("id", flat=True),
                    )
                )
            except (ValueError, TypeError):
                pass

        # Filter by specific pack
        pack_id = self.request.query_params.get("pack", None)
        if pack_id:
            try:
                queryset = queryset.filter(entity_type="pack", entity_id=int(pack_id))
            except (ValueError, TypeError):
                pass

        # Filter by specific shipment
        shipment_id = self.request.query_params.get("shipment", None)
        if shipment_id:
            try:
                shipment_id = int(shipment_id)
                # Include events for the shipment itself and its packs
                pack_ids = m.ShipmentPack.objects.filter(
                    shipment_id=shipment_id
                ).values_list("pack_id", flat=True)
                queryset = queryset.filter(
                    Q(entity_type="shipment", entity_id=shipment_id)
                    | Q(entity_type="pack", entity_id__in=pack_ids)
                )
            except (ValueError, TypeError):
                pass

        # Filter by critical events only
        critical_only = self.request.query_params.get("critical_only", None)
        if critical_only and critical_only.lower() in ["true", "1"]:
            queryset = queryset.filter(severity="critical")

        # Filter by alert events only
        alert_only = self.request.query_params.get("alert_only", None)
        if alert_only and alert_only.lower() in ["true", "1"]:
            queryset = queryset.filter(
                Q(severity__in=["high", "critical"])
                | Q(
                    event_type__in=["temperature_alert", "damaged", "recalled", "error"]
                )
            )

        # Filter by recent events (last N days)
        recent_days = self.request.query_params.get("recent_days", None)
        if recent_days:
            try:
                days = int(recent_days)
                from datetime import timedelta
                from django.utils import timezone

                cutoff_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(timestamp__gte=cutoff_date)
            except (ValueError, TypeError):
                pass

        return queryset.order_by("-timestamp", "-id")

    def perform_create(self, serializer):
        """Create a new event with additional context."""
        # Add request context if available
        extra_data = {}

        if self.request:
            extra_data["ip_address"] = self.get_client_ip()
            extra_data["user_agent"] = self.request.META.get("HTTP_USER_AGENT", "")

            # Set user if not provided and user is authenticated
            if (
                not serializer.validated_data.get("user")
                and self.request.user.is_authenticated
            ):
                extra_data["user"] = self.request.user

        serializer.save(**extra_data)

    def get_client_ip(self):
        """Get the client IP address from the request."""
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR")
        return ip


class EventDetailUpdateView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a specific event."""

    queryset = m.Event.objects.select_related("user", "content_type").all()
    permission_classes = [IsAuthenticated]
    serializer_class = s.EventDetailSerializer

    def get_queryset(self):
        """Include soft-deleted events for detail view (admins might need to see them)."""
        return m.Event.all_objects.select_related("user", "content_type").all()

    def perform_update(self, serializer):
        """Update event with additional context."""
        # Add request context if available
        extra_data = {}

        if self.request:
            extra_data["ip_address"] = self.get_client_ip()
            extra_data["user_agent"] = self.request.META.get("HTTP_USER_AGENT", "")

        serializer.save(**extra_data)

    def get_client_ip(self):
        """Get the client IP address from the request."""
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR")
        return ip


class EventDeleteView(generics.DestroyAPIView):
    """Soft delete an event (admin only)."""

    queryset = m.Event.objects.all()
    permission_classes = [IsAuthenticated, p.IsAdminRole]

    def get_queryset(self):
        """Only allow deletion of non-deleted events."""
        return super().get_queryset().filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        """Soft delete the event."""
        instance.delete()  # This will use the soft delete from BaseModel

    def destroy(self, request, *args, **kwargs):
        """Override to return proper response after soft delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Event deleted successfully"}, status=status.HTTP_200_OK
        )
