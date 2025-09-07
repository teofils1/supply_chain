from __future__ import annotations

import contextlib
from datetime import date

from django.db.models import Prefetch, Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .. import models as m
from .. import permissions as p
from .. import serializers as s


class ShipmentListCreateView(generics.ListCreateAPIView):
    """List all shipments or create a new shipment."""

    queryset = m.Shipment.objects.prefetch_related(
        Prefetch(
            "shipment_packs",
            queryset=m.ShipmentPack.objects.select_related("pack__batch__product"),
        )
    ).all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return s.ShipmentCreateSerializer
        return s.ShipmentListSerializer

    def get_queryset(self):
        """Filter shipments based on query parameters."""
        queryset = super().get_queryset()

        # Search functionality
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(tracking_number__icontains=search)
                | Q(origin_name__icontains=search)
                | Q(destination_name__icontains=search)
                | Q(origin_city__icontains=search)
                | Q(destination_city__icontains=search)
                | Q(carrier__icontains=search)
                | Q(billing_reference__icontains=search)
                | Q(notes__icontains=search)
                | Q(packs__serial_number__icontains=search)
                | Q(packs__batch__lot_number__icontains=search)
                | Q(packs__batch__product__name__icontains=search)
                | Q(packs__batch__product__gtin__icontains=search)
            ).distinct()

        # Filter by status
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by carrier
        carrier_filter = self.request.query_params.get("carrier", None)
        if carrier_filter:
            queryset = queryset.filter(carrier=carrier_filter)

        # Filter by service type
        service_type_filter = self.request.query_params.get("service_type", None)
        if service_type_filter:
            queryset = queryset.filter(service_type=service_type_filter)

        # Filter by temperature requirement
        temp_requirement_filter = self.request.query_params.get(
            "temperature_requirement", None
        )
        if temp_requirement_filter:
            queryset = queryset.filter(temperature_requirement=temp_requirement_filter)

        # Filter by origin city/state
        origin_city = self.request.query_params.get("origin_city", None)
        if origin_city:
            queryset = queryset.filter(origin_city__icontains=origin_city)

        origin_state = self.request.query_params.get("origin_state", None)
        if origin_state:
            queryset = queryset.filter(origin_state__icontains=origin_state)

        # Filter by destination city/state
        destination_city = self.request.query_params.get("destination_city", None)
        if destination_city:
            queryset = queryset.filter(destination_city__icontains=destination_city)

        destination_state = self.request.query_params.get("destination_state", None)
        if destination_state:
            queryset = queryset.filter(destination_state__icontains=destination_state)

        # Filter by shipped date range
        shipped_from = self.request.query_params.get("shipped_from", None)
        shipped_to = self.request.query_params.get("shipped_to", None)

        if shipped_from:
            try:
                from datetime import datetime

                shipped_from_date = datetime.strptime(shipped_from, "%Y-%m-%d").date()
                queryset = queryset.filter(shipped_date__date__gte=shipped_from_date)
            except ValueError:
                pass

        if shipped_to:
            try:
                from datetime import datetime

                shipped_to_date = datetime.strptime(shipped_to, "%Y-%m-%d").date()
                queryset = queryset.filter(shipped_date__date__lte=shipped_to_date)
            except ValueError:
                pass

        # Filter by estimated delivery date range
        estimated_delivery_from = self.request.query_params.get(
            "estimated_delivery_from", None
        )
        estimated_delivery_to = self.request.query_params.get(
            "estimated_delivery_to", None
        )

        if estimated_delivery_from:
            try:
                from datetime import datetime

                est_from_date = datetime.strptime(
                    estimated_delivery_from, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    estimated_delivery_date__date__gte=est_from_date
                )
            except ValueError:
                pass

        if estimated_delivery_to:
            try:
                from datetime import datetime

                est_to_date = datetime.strptime(
                    estimated_delivery_to, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(
                    estimated_delivery_date__date__lte=est_to_date
                )
            except ValueError:
                pass

        # Filter by pack
        pack_id = self.request.query_params.get("pack", None)
        if pack_id:
            with contextlib.suppress(ValueError, TypeError):
                queryset = queryset.filter(packs__id=int(pack_id))

        # Filter by batch (through pack relationship)
        batch_id = self.request.query_params.get("batch", None)
        if batch_id:
            with contextlib.suppress(ValueError, TypeError):
                queryset = queryset.filter(packs__batch__id=int(batch_id))

        # Filter by product (through pack->batch relationship)
        product_id = self.request.query_params.get("product", None)
        if product_id:
            with contextlib.suppress(ValueError, TypeError):
                queryset = queryset.filter(packs__batch__product__id=int(product_id))

        # Filter by delivery status
        delivery_status = self.request.query_params.get("delivery_status", None)
        if delivery_status == "delivered":
            queryset = queryset.filter(
                Q(status="delivered") | Q(actual_delivery_date__isnull=False)
            )
        elif delivery_status == "in_transit":
            queryset = queryset.filter(
                status__in=["picked_up", "in_transit", "out_for_delivery"]
            )
        elif delivery_status == "pending":
            queryset = queryset.filter(status__in=["pending", "confirmed"])
        elif delivery_status == "overdue":
            # Shipments past estimated delivery date but not delivered
            today = date.today()
            queryset = queryset.filter(
                estimated_delivery_date__date__lt=today,
                status__in=["picked_up", "in_transit", "out_for_delivery"],
            )

        # Filter by special handling
        special_handling = self.request.query_params.get("special_handling", None)
        if special_handling is not None:
            if special_handling.lower() in ["true", "1"]:
                queryset = queryset.filter(special_handling_required=True)
            elif special_handling.lower() in ["false", "0"]:
                queryset = queryset.filter(special_handling_required=False)

        return queryset.order_by("-created_at", "tracking_number")

    def perform_create(self, serializer):
        """Create a new shipment."""
        serializer.save()


class ShipmentDetailUpdateView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a specific shipment."""

    queryset = m.Shipment.objects.prefetch_related(
        Prefetch(
            "shipment_packs",
            queryset=m.ShipmentPack.objects.select_related("pack__batch__product"),
        )
    ).all()
    permission_classes = [IsAuthenticated]
    serializer_class = s.ShipmentDetailSerializer

    def get_queryset(self):
        """Include soft-deleted shipments for detail view (admins might need to see them)."""
        return m.Shipment.all_objects.prefetch_related(
            Prefetch(
                "shipment_packs",
                queryset=m.ShipmentPack.objects.select_related("pack__batch__product"),
            )
        ).all()

    def perform_update(self, serializer):
        """Update shipment and handle pack relationships if needed."""
        # Note: For updating pack relationships, we'd need additional logic
        # This could be implemented as a separate endpoint or enhanced here
        serializer.save()


class ShipmentDeleteView(generics.DestroyAPIView):
    """Soft delete a shipment."""

    queryset = m.Shipment.objects.all()
    permission_classes = [IsAuthenticated, p.IsAdminRole]

    def get_queryset(self):
        """Only allow deletion of non-delivered shipments."""
        return (
            super()
            .get_queryset()
            .filter(
                deleted_at__isnull=True,
                status__in=["pending", "confirmed", "cancelled"],
            )
        )

    def perform_destroy(self, instance):
        """Soft delete the shipment and update pack statuses."""
        # Reset pack statuses for packs in this shipment
        for shipment_pack in instance.shipment_packs.all():
            pack = shipment_pack.pack
            # Reset pack status to active if it was shipped due to this shipment
            if (
                pack.status in ["shipped", "delivered"]
                and not pack.pack_shipments.exclude(shipment=instance)
                .filter(
                    shipment__status__in=[
                        "picked_up",
                        "in_transit",
                        "out_for_delivery",
                        "delivered",
                    ]
                )
                .exists()
            ):
                pack.status = "active"
                pack.shipped_date = None
                pack.delivered_date = None
                pack.save()

        instance.delete()  # This will use the soft delete from BaseModel

    def destroy(self, request, *args, **kwargs):
        """Override to return proper response after soft delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Shipment deleted successfully"}, status=status.HTTP_200_OK
        )
