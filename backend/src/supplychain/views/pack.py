from __future__ import annotations

from datetime import date, timedelta
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .. import models as m
from .. import permissions as p
from .. import serializers as s


class PackListCreateView(generics.ListCreateAPIView):
    """List all packs or create a new pack."""
    
    queryset = m.Pack.objects.select_related('batch__product').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return s.PackCreateSerializer
        return s.PackListSerializer
    
    def get_queryset(self):
        """Filter packs based on query parameters."""
        queryset = super().get_queryset()
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(serial_number__icontains=search) |
                Q(batch__lot_number__icontains=search) |
                Q(batch__product__name__icontains=search) |
                Q(batch__product__gtin__icontains=search) |
                Q(location__icontains=search) |
                Q(warehouse_section__icontains=search) |
                Q(customer_reference__icontains=search) |
                Q(tracking_number__icontains=search) |
                Q(regulatory_code__icontains=search)
            )
        
        # Filter by batch
        batch_id = self.request.query_params.get('batch', None)
        if batch_id:
            try:
                queryset = queryset.filter(batch_id=int(batch_id))
            except (ValueError, TypeError):
                pass
        
        # Filter by product (through batch relationship)
        product_id = self.request.query_params.get('product', None)
        if product_id:
            try:
                queryset = queryset.filter(batch__product_id=int(product_id))
            except (ValueError, TypeError):
                pass
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by pack type
        pack_type_filter = self.request.query_params.get('pack_type', None)
        if pack_type_filter:
            queryset = queryset.filter(pack_type=pack_type_filter)
        
        # Filter by location
        location_filter = self.request.query_params.get('location', None)
        if location_filter:
            queryset = queryset.filter(location__icontains=location_filter)
        
        # Filter by expiry date range (using effective expiry date)
        expiry_from = self.request.query_params.get('expiry_from', None)
        expiry_to = self.request.query_params.get('expiry_to', None)
        
        if expiry_from:
            try:
                from datetime import datetime
                expiry_from_date = datetime.strptime(expiry_from, '%Y-%m-%d').date()
                # Filter by pack-specific expiry date or batch expiry date
                queryset = queryset.filter(
                    Q(expiry_date__gte=expiry_from_date) |
                    Q(expiry_date__isnull=True, batch__expiry_date__gte=expiry_from_date)
                )
            except ValueError:
                pass
        
        if expiry_to:
            try:
                from datetime import datetime
                expiry_to_date = datetime.strptime(expiry_to, '%Y-%m-%d').date()
                # Filter by pack-specific expiry date or batch expiry date
                queryset = queryset.filter(
                    Q(expiry_date__lte=expiry_to_date) |
                    Q(expiry_date__isnull=True, batch__expiry_date__lte=expiry_to_date)
                )
            except ValueError:
                pass
        
        # Filter by shipping date range
        shipped_from = self.request.query_params.get('shipped_from', None)
        shipped_to = self.request.query_params.get('shipped_to', None)
        
        if shipped_from:
            try:
                from datetime import datetime
                shipped_from_date = datetime.strptime(shipped_from, '%Y-%m-%d').date()
                queryset = queryset.filter(shipped_date__date__gte=shipped_from_date)
            except ValueError:
                pass
        
        if shipped_to:
            try:
                from datetime import datetime
                shipped_to_date = datetime.strptime(shipped_to, '%Y-%m-%d').date()
                queryset = queryset.filter(shipped_date__date__lte=shipped_to_date)
            except ValueError:
                pass
        
        # Filter by quality control status
        qc_passed = self.request.query_params.get('qc_passed', None)
        if qc_passed is not None:
            if qc_passed.lower() in ['true', '1']:
                queryset = queryset.filter(quality_control_passed=True)
            elif qc_passed.lower() in ['false', '0']:
                queryset = queryset.filter(quality_control_passed=False)
        
        # Filter by shipping status
        shipping_status = self.request.query_params.get('shipping_status', None)
        if shipping_status == 'shipped':
            queryset = queryset.filter(
                Q(status__in=['shipped', 'delivered']) | Q(shipped_date__isnull=False)
            )
        elif shipping_status == 'delivered':
            queryset = queryset.filter(
                Q(status='delivered') | Q(delivered_date__isnull=False)
            )
        elif shipping_status == 'not_shipped':
            queryset = queryset.filter(
                shipped_date__isnull=True,
                status__in=['active', 'quarantined']
            )
        
        # Filter by expiry status
        expiry_status = self.request.query_params.get('expiry_status', None)
        if expiry_status == 'expired':
            today = date.today()
            queryset = queryset.filter(
                Q(expiry_date__lt=today) |
                Q(expiry_date__isnull=True, batch__expiry_date__lt=today)
            )
        elif expiry_status == 'expiring_soon':
            # Expiring within 30 days
            today = date.today()
            soon_date = today + timedelta(days=30)
            queryset = queryset.filter(
                Q(expiry_date__gte=today, expiry_date__lte=soon_date) |
                Q(expiry_date__isnull=True, batch__expiry_date__gte=today, batch__expiry_date__lte=soon_date)
            )
        elif expiry_status == 'active':
            today = date.today()
            queryset = queryset.filter(
                Q(expiry_date__gte=today) |
                Q(expiry_date__isnull=True, batch__expiry_date__gte=today)
            )
        
        return queryset.order_by('-created_at', 'serial_number')
    
    def perform_create(self, serializer):
        """Create a new pack."""
        serializer.save()


class PackDetailUpdateView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a specific pack."""
    
    queryset = m.Pack.objects.select_related('batch__product').all()
    permission_classes = [IsAuthenticated]
    serializer_class = s.PackDetailSerializer
    
    def get_queryset(self):
        """Include soft-deleted packs for detail view (admins might need to see them)."""
        return m.Pack.all_objects.select_related('batch__product').all()


class PackDeleteView(generics.DestroyAPIView):
    """Soft delete a pack."""
    
    queryset = m.Pack.objects.all()
    permission_classes = [IsAuthenticated, p.IsAdminRole]
    
    def get_queryset(self):
        """Only allow deletion of active packs."""
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def perform_destroy(self, instance):
        """Soft delete the pack."""
        instance.delete()  # This will use the soft delete from BaseModel
    
    def destroy(self, request, *args, **kwargs):
        """Override to return proper response after soft delete."""
        instance = self.get_object()
        
        # Check if pack is part of an active shipment (if Shipment model exists)
        # This would be added later when Shipment model is implemented
        
        self.perform_destroy(instance)
        return Response(
            {"message": "Pack deleted successfully"}, 
            status=status.HTTP_200_OK
        )
