#!/usr/bin/env python3
"""
Script to create sample shipments for testing the shipment view feature.
"""

import os
import sys
import django
from datetime import date, timedelta, datetime
from decimal import Decimal

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from supplychain.models import Pack, Shipment, ShipmentPack

def create_sample_shipments():
    """Create sample shipments for testing."""
    
    # Get existing packs that are available for shipping
    available_packs = Pack.objects.filter(
        status__in=['active', 'quarantined'],
        deleted_at__isnull=True
    ).select_related('batch__product')
    
    if not available_packs.exists():
        print("No available packs found. Please create packs first.")
        return
    
    sample_shipments = []
    
    # Shipment 1: Standard delivery with multiple packs
    aspirin_packs = available_packs.filter(batch__product__name__icontains="Aspirin")[:2]
    if aspirin_packs:
        sample_shipments.append({
            'shipment_data': {
                'tracking_number': 'SHP-ASP-001',
                'status': 'in_transit',
                'carrier': 'fedex',
                'service_type': 'standard',
                'origin_name': 'PharmaCorp Manufacturing',
                'origin_address_line1': '123 Industrial Blvd',
                'origin_city': 'Chicago',
                'origin_state': 'IL',
                'origin_postal_code': '60601',
                'origin_country': 'USA',
                'destination_name': 'MediSupply Distribution Center',
                'destination_address_line1': '456 Warehouse Ave',
                'destination_city': 'Atlanta',
                'destination_state': 'GA',
                'destination_postal_code': '30301',
                'destination_country': 'USA',
                'shipped_date': datetime.now() - timedelta(days=2),
                'estimated_delivery_date': datetime.now() + timedelta(days=1),
                'temperature_requirement': 'ambient',
                'shipping_cost': Decimal('45.99'),
                'currency': 'USD',
                'billing_reference': 'INV-2024-001',
                'notes': 'Standard pharmaceutical shipment. Handle with care.'
            },
            'pack_ids': [pack.id for pack in aspirin_packs]
        })
    
    # Shipment 2: Express delivery - single pack
    amoxicillin_packs = available_packs.filter(batch__product__name__icontains="Amoxicillin")[:1]
    if amoxicillin_packs:
        sample_shipments.append({
            'shipment_data': {
                'tracking_number': 'SHP-AMX-002',
                'status': 'delivered',
                'carrier': 'ups',
                'service_type': 'express',
                'origin_name': 'PharmaCorp Manufacturing',
                'origin_address_line1': '123 Industrial Blvd',
                'origin_city': 'Chicago',
                'origin_state': 'IL',
                'origin_postal_code': '60601',
                'origin_country': 'USA',
                'destination_name': 'City General Hospital',
                'destination_address_line1': '789 Medical Center Dr',
                'destination_city': 'New York',
                'destination_state': 'NY',
                'destination_postal_code': '10001',
                'destination_country': 'USA',
                'shipped_date': datetime.now() - timedelta(days=3),
                'estimated_delivery_date': datetime.now() - timedelta(days=1),
                'actual_delivery_date': datetime.now() - timedelta(days=1),
                'temperature_requirement': 'ambient',
                'shipping_cost': Decimal('89.50'),
                'currency': 'USD',
                'billing_reference': 'INV-2024-002',
                'notes': 'Express delivery for urgent medical need.'
            },
            'pack_ids': [pack.id for pack in amoxicillin_packs]
        })
    
    # Shipment 3: Cold chain shipment
    insulin_packs = available_packs.filter(batch__product__name__icontains="Insulin")[:1]
    if insulin_packs:
        sample_shipments.append({
            'shipment_data': {
                'tracking_number': 'SHP-INS-003',
                'status': 'picked_up',
                'carrier': 'dhl',
                'service_type': 'cold_chain',
                'origin_name': 'BioPharm Cold Storage',
                'origin_address_line1': '321 Cold Chain Blvd',
                'origin_city': 'Boston',
                'origin_state': 'MA',
                'origin_postal_code': '02101',
                'origin_country': 'USA',
                'destination_name': 'Diabetes Care Clinic',
                'destination_address_line1': '654 Healthcare Way',
                'destination_city': 'Miami',
                'destination_state': 'FL',
                'destination_postal_code': '33101',
                'destination_country': 'USA',
                'shipped_date': datetime.now() - timedelta(hours=6),
                'estimated_delivery_date': datetime.now() + timedelta(days=2),
                'temperature_requirement': 'cool',
                'special_handling_required': True,
                'special_instructions': 'Maintain 2-8°C throughout transport. Temperature monitoring required.',
                'shipping_cost': Decimal('125.00'),
                'currency': 'USD',
                'billing_reference': 'INV-2024-003',
                'notes': 'Cold chain shipment - critical temperature control required.'
            },
            'pack_ids': [pack.id for pack in insulin_packs]
        })
    
    # Shipment 4: Pending shipment with multiple products
    mixed_packs = []
    hydrocortisone_packs = available_packs.filter(batch__product__name__icontains="Hydrocortisone")[:1]
    vitamin_packs = available_packs.filter(batch__product__name__icontains="Vitamin")[:1]
    mixed_packs.extend(hydrocortisone_packs)
    mixed_packs.extend(vitamin_packs)
    
    if mixed_packs:
        sample_shipments.append({
            'shipment_data': {
                'tracking_number': 'SHP-MIX-004',
                'status': 'pending',
                'carrier': 'usps',
                'service_type': 'ground',
                'origin_name': 'Regional Distribution Hub',
                'origin_address_line1': '987 Distribution Pkwy',
                'origin_city': 'Dallas',
                'origin_state': 'TX',
                'origin_postal_code': '75201',
                'origin_country': 'USA',
                'destination_name': 'Community Pharmacy Network',
                'destination_address_line1': '147 Main Street',
                'destination_city': 'Phoenix',
                'destination_state': 'AZ',
                'destination_postal_code': '85001',
                'destination_country': 'USA',
                'estimated_delivery_date': datetime.now() + timedelta(days=5),
                'temperature_requirement': 'ambient',
                'shipping_cost': Decimal('32.75'),
                'currency': 'USD',
                'billing_reference': 'INV-2024-004',
                'notes': 'Mixed product shipment to pharmacy network.'
            },
            'pack_ids': [pack.id for pack in mixed_packs]
        })
    
    # Shipment 5: Cancelled shipment
    remaining_packs = available_packs.exclude(
        id__in=[pack.id for shipment in sample_shipments for pack in Pack.objects.filter(id__in=shipment['pack_ids'])]
    )[:1]
    
    if remaining_packs:
        sample_shipments.append({
            'shipment_data': {
                'tracking_number': 'SHP-CAN-005',
                'status': 'cancelled',
                'carrier': 'local',
                'service_type': 'standard',
                'origin_name': 'Local Warehouse',
                'origin_address_line1': '555 Storage St',
                'origin_city': 'Denver',
                'origin_state': 'CO',
                'origin_postal_code': '80201',
                'origin_country': 'USA',
                'destination_name': 'Mountain View Clinic',
                'destination_address_line1': '888 Mountain Rd',
                'destination_city': 'Boulder',
                'destination_state': 'CO',
                'destination_postal_code': '80301',
                'destination_country': 'USA',
                'temperature_requirement': 'ambient',
                'notes': 'Shipment cancelled due to recipient request.'
            },
            'pack_ids': [pack.id for pack in remaining_packs]
        })
    
    # Shipment 6: Overdue shipment (past estimated delivery)
    if len(available_packs) > 5:
        overdue_packs = available_packs[5:6]
        sample_shipments.append({
            'shipment_data': {
                'tracking_number': 'SHP-OVR-006',
                'status': 'in_transit',
                'carrier': 'amazon',
                'service_type': 'standard',
                'origin_name': 'Amazon Fulfillment Center',
                'origin_address_line1': '999 Fulfillment Way',
                'origin_city': 'Seattle',
                'origin_state': 'WA',
                'origin_postal_code': '98101',
                'origin_country': 'USA',
                'destination_name': 'Rural Health Center',
                'destination_address_line1': '111 Country Road',
                'destination_city': 'Spokane',
                'destination_state': 'WA',
                'destination_postal_code': '99201',
                'destination_country': 'USA',
                'shipped_date': datetime.now() - timedelta(days=5),
                'estimated_delivery_date': datetime.now() - timedelta(days=2),  # Overdue
                'temperature_requirement': 'ambient',
                'shipping_cost': Decimal('28.99'),
                'currency': 'USD',
                'billing_reference': 'INV-2024-006',
                'notes': 'Shipment delayed due to weather conditions.'
            },
            'pack_ids': [pack.id for pack in overdue_packs]
        })
    
    created_count = 0
    for shipment_info in sample_shipments:
        shipment_data = shipment_info['shipment_data']
        pack_ids = shipment_info['pack_ids']
        
        # Check if shipment already exists
        if not Shipment.objects.filter(tracking_number=shipment_data['tracking_number']).exists():
            # Create shipment
            shipment = Shipment.objects.create(**shipment_data)
            
            # Create ShipmentPack relationships
            for pack_id in pack_ids:
                ShipmentPack.objects.create(
                    shipment=shipment,
                    pack_id=pack_id,
                    quantity_shipped=1
                )
            
            print(f"Created shipment: {shipment.tracking_number} - {shipment.status} ({len(pack_ids)} packs)")
            created_count += 1
        else:
            print(f"Shipment {shipment_data['tracking_number']} already exists, skipping...")
    
    print(f"\nCreated {created_count} new shipments.")
    print(f"Total shipments in database: {Shipment.objects.count()}")

if __name__ == '__main__':
    create_sample_shipments()
