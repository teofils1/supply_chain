from __future__ import annotations

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .. import models as m
from .. import permissions as p
from .. import serializers as s


class ProductListCreateView(generics.ListCreateAPIView):
    """List all products or create a new product."""

    queryset = m.Product.objects.all()
    permission_classes = [IsAuthenticated, p.RoleBasedCRUDPermission]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return s.ProductCreateSerializer
        return s.ProductListSerializer

    def get_queryset(self):
        """Filter products based on query parameters."""
        queryset = super().get_queryset()

        # Search functionality
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(gtin__icontains=search)
                | Q(manufacturer__icontains=search)
                | Q(description__icontains=search)
            )

        # Filter by status
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by form
        form_filter = self.request.query_params.get("form", None)
        if form_filter:
            queryset = queryset.filter(form=form_filter)

        # Filter by manufacturer
        manufacturer_filter = self.request.query_params.get("manufacturer", None)
        if manufacturer_filter:
            queryset = queryset.filter(manufacturer__icontains=manufacturer_filter)

        return queryset.order_by("name", "gtin")

    def perform_create(self, serializer):
        """Create a new product."""
        serializer.save()


class ProductDetailUpdateView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a specific product."""

    queryset = m.Product.objects.all()
    permission_classes = [IsAuthenticated, p.RoleBasedCRUDPermission]
    serializer_class = s.ProductDetailSerializer

    def get_queryset(self):
        """Include soft-deleted products for detail view (admins might need to see them)."""
        return m.Product.all_objects.all()


class ProductDeleteView(generics.DestroyAPIView):
    """Soft delete a product."""

    queryset = m.Product.objects.all()
    permission_classes = [IsAuthenticated, p.RoleBasedCRUDPermission]

    def get_queryset(self):
        """Only allow deletion of active products."""
        return super().get_queryset().filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        """Soft delete the product."""
        instance.delete()  # This will use the soft delete from BaseModel

    def destroy(self, request, *args, **kwargs):
        """Override to return proper response after soft delete."""
        instance = self.get_object()

        # Check if product has associated batches/packs (if those models exist)
        # This would be added later when Batch and Pack models are implemented

        self.perform_destroy(instance)
        return Response(
            {"message": "Product deleted successfully"}, status=status.HTTP_200_OK
        )
