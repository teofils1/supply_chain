from __future__ import annotations

import contextlib
from datetime import date, timedelta

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .. import models as m
from .. import permissions as p
from .. import serializers as s


class BatchListCreateView(generics.ListCreateAPIView):
    """List all batches or create a new batch."""

    queryset = m.Batch.objects.select_related("product").all()
    permission_classes = [IsAuthenticated, p.RoleBasedCRUDPermission]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return s.BatchCreateSerializer
        return s.BatchListSerializer

    def get_queryset(self):
        """Filter batches based on query parameters."""
        queryset = super().get_queryset()

        # Search functionality
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(lot_number__icontains=search)
                | Q(product__name__icontains=search)
                | Q(product__gtin__icontains=search)
                | Q(manufacturing_location__icontains=search)
                | Q(manufacturing_facility__icontains=search)
                | Q(quality_control_notes__icontains=search)
            )

        # Filter by product
        product_id = self.request.query_params.get("product", None)
        if product_id:
            with contextlib.suppress(ValueError, TypeError):
                queryset = queryset.filter(product_id=int(product_id))

        # Filter by status
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by manufacturing location
        location_filter = self.request.query_params.get("location", None)
        if location_filter:
            queryset = queryset.filter(
                manufacturing_location__icontains=location_filter
            )

        # Filter by expiry date range
        expiry_from = self.request.query_params.get("expiry_from", None)
        expiry_to = self.request.query_params.get("expiry_to", None)

        if expiry_from:
            try:
                from datetime import datetime

                expiry_from_date = datetime.strptime(expiry_from, "%Y-%m-%d").date()
                queryset = queryset.filter(expiry_date__gte=expiry_from_date)
            except ValueError:
                pass

        if expiry_to:
            try:
                from datetime import datetime

                expiry_to_date = datetime.strptime(expiry_to, "%Y-%m-%d").date()
                queryset = queryset.filter(expiry_date__lte=expiry_to_date)
            except ValueError:
                pass

        # Filter by manufacturing date range
        mfg_from = self.request.query_params.get("mfg_from", None)
        mfg_to = self.request.query_params.get("mfg_to", None)

        if mfg_from:
            try:
                from datetime import datetime

                mfg_from_date = datetime.strptime(mfg_from, "%Y-%m-%d").date()
                queryset = queryset.filter(manufacturing_date__gte=mfg_from_date)
            except ValueError:
                pass

        if mfg_to:
            try:
                from datetime import datetime

                mfg_to_date = datetime.strptime(mfg_to, "%Y-%m-%d").date()
                queryset = queryset.filter(manufacturing_date__lte=mfg_to_date)
            except ValueError:
                pass

        # Filter by quality control status
        qc_passed = self.request.query_params.get("qc_passed", None)
        if qc_passed is not None:
            if qc_passed.lower() in ["true", "1"]:
                queryset = queryset.filter(quality_control_passed=True)
            elif qc_passed.lower() in ["false", "0"]:
                queryset = queryset.filter(quality_control_passed=False)

        # Filter by expiry status
        expiry_status = self.request.query_params.get("expiry_status", None)
        if expiry_status == "expired":
            queryset = queryset.filter(expiry_date__lt=date.today())
        elif expiry_status == "expiring_soon":
            # Expiring within 30 days
            soon_date = date.today() + timedelta(days=30)
            queryset = queryset.filter(
                expiry_date__gte=date.today(), expiry_date__lte=soon_date
            )
        elif expiry_status == "active":
            queryset = queryset.filter(expiry_date__gte=date.today())

        return queryset.order_by("-manufacturing_date", "lot_number")

    def perform_create(self, serializer):
        """Create a new batch."""
        serializer.save()


class BatchDetailUpdateView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a specific batch."""

    queryset = m.Batch.objects.select_related("product").all()
    permission_classes = [IsAuthenticated, p.RoleBasedCRUDPermission]
    serializer_class = s.BatchDetailSerializer

    def get_queryset(self):
        """Include soft-deleted batches for detail view (admins might need to see them)."""
        return m.Batch.all_objects.select_related("product").all()


class BatchDeleteView(generics.DestroyAPIView):
    """Soft delete a batch."""

    queryset = m.Batch.objects.all()
    permission_classes = [IsAuthenticated, p.RoleBasedCRUDPermission]

    def get_queryset(self):
        """Only allow deletion of active batches."""
        return super().get_queryset().filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        """Soft delete the batch."""
        instance.delete()  # This will use the soft delete from BaseModel

    def destroy(self, request, *args, **kwargs):
        """Override to return proper response after soft delete."""
        instance = self.get_object()

        # Check if batch has associated packs (if Pack model exists)
        # This would be added later when Pack model is implemented

        self.perform_destroy(instance)
        return Response(
            {"message": "Batch deleted successfully"}, status=status.HTTP_200_OK
        )
