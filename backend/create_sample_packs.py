#!/usr/bin/env python3
"""
Script to create sample packs for testing the pack view feature.
"""

import os
import sys
import django
from datetime import date, timedelta, datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from supplychain.models import Batch, Pack

def create_sample_packs():
    """Create sample packs for testing."""
    
    # Get existing batches
    batches = Batch.objects.all()
    if not batches.exists():
        print("No batches found. Please create batches first.")
        return
    
    sample_packs = []
    
    # Aspirin batches
    aspirin_batches = batches.filter(product__name__icontains="Aspirin")
    for batch in aspirin_batches[:2]:  # Take first 2 aspirin batches
        sample_packs.extend([
            {
                'batch': batch,
                'serial_number': f'ASP-{batch.lot_number}-001',
                'pack_size': 100,
                'pack_type': 'bottle',
                'status': 'active',
                'location': 'Warehouse A',
                'warehouse_section': 'A-01-15',
                'quality_control_passed': True,
                'quality_control_notes': 'All quality checks passed. Ready for distribution.',
                'regulatory_code': f'REG-ASP-{batch.lot_number}-001'
            },
            {
                'batch': batch,
                'serial_number': f'ASP-{batch.lot_number}-002',
                'pack_size': 100,
                'pack_type': 'bottle',
                'status': 'shipped',
                'location': 'In Transit',
                'shipped_date': datetime.now() - timedelta(days=2),
                'tracking_number': f'TRK{batch.lot_number}002',
                'customer_reference': 'CUST-001',
                'quality_control_passed': True
            },
            {
                'batch': batch,
                'serial_number': f'ASP-{batch.lot_number}-003',
                'pack_size': 50,
                'pack_type': 'box',
                'status': 'delivered',
                'location': 'Customer Site',
                'shipped_date': datetime.now() - timedelta(days=5),
                'delivered_date': datetime.now() - timedelta(days=3),
                'tracking_number': f'TRK{batch.lot_number}003',
                'customer_reference': 'CUST-002',
                'quality_control_passed': True
            }
        ])
    
    # Amoxicillin batches
    amoxicillin_batches = batches.filter(product__name__icontains="Amoxicillin")
    for batch in amoxicillin_batches[:2]:  # Take first 2 amoxicillin batches
        sample_packs.extend([
            {
                'batch': batch,
                'serial_number': f'AMX-{batch.lot_number}-001',
                'pack_size': 30,
                'pack_type': 'blister',
                'status': 'active',
                'location': 'Warehouse B',
                'warehouse_section': 'B-02-08',
                'quality_control_passed': True,
                'quality_control_notes': 'Blister pack integrity verified.',
                'regulatory_code': f'REG-AMX-{batch.lot_number}-001'
            },
            {
                'batch': batch,
                'serial_number': f'AMX-{batch.lot_number}-002',
                'pack_size': 30,
                'pack_type': 'blister',
                'status': 'quarantined',
                'location': 'QC Lab',
                'warehouse_section': 'QC-01',
                'quality_control_passed': False,
                'quality_control_notes': 'Minor packaging defect detected. Under investigation.'
            }
        ])
    
    # Insulin batches
    insulin_batches = batches.filter(product__name__icontains="Insulin")
    for batch in insulin_batches[:1]:  # Take first insulin batch
        sample_packs.extend([
            {
                'batch': batch,
                'serial_number': f'INS-{batch.lot_number}-001',
                'pack_size': 1,
                'pack_type': 'vial',
                'status': 'active',
                'location': 'Cold Storage A',
                'warehouse_section': 'CS-A-01',
                'quality_control_passed': True,
                'quality_control_notes': 'Cold chain maintained. Temperature logs verified.',
                'regulatory_code': f'REG-INS-{batch.lot_number}-001'
            },
            {
                'batch': batch,
                'serial_number': f'INS-{batch.lot_number}-002',
                'pack_size': 1,
                'pack_type': 'vial',
                'status': 'shipped',
                'location': 'Cold Chain Transport',
                'shipped_date': datetime.now() - timedelta(hours=6),
                'tracking_number': f'COLD{batch.lot_number}002',
                'customer_reference': 'HOSP-001',
                'quality_control_passed': True,
                'quality_control_notes': 'Special cold chain shipping requirements.'
            }
        ])
    
    # Hydrocortisone batches
    hydrocortisone_batches = batches.filter(product__name__icontains="Hydrocortisone")
    for batch in hydrocortisone_batches[:1]:  # Take first hydrocortisone batch
        sample_packs.extend([
            {
                'batch': batch,
                'serial_number': f'HYD-{batch.lot_number}-001',
                'pack_size': 1,
                'pack_type': 'tube',
                'status': 'active',
                'location': 'Warehouse C',
                'warehouse_section': 'C-03-12',
                'quality_control_passed': True,
                'quality_control_notes': 'Tube seal integrity verified.',
                'regulatory_code': f'REG-HYD-{batch.lot_number}-001'
            },
            {
                'batch': batch,
                'serial_number': f'HYD-{batch.lot_number}-002',
                'pack_size': 1,
                'pack_type': 'tube',
                'status': 'damaged',
                'location': 'Damage Assessment',
                'warehouse_section': 'DA-01',
                'quality_control_passed': False,
                'quality_control_notes': 'Tube damaged during handling. Marked for disposal.'
            }
        ])
    
    # Cough Syrup batches (expired product)
    cough_batches = batches.filter(product__name__icontains="Cough")
    for batch in cough_batches[:1]:  # Take first cough syrup batch
        sample_packs.extend([
            {
                'batch': batch,
                'serial_number': f'CS-{batch.lot_number}-001',
                'pack_size': 1,
                'pack_type': 'bottle',
                'status': 'recalled',
                'location': 'Recall Storage',
                'warehouse_section': 'RC-01',
                'quality_control_passed': True,
                'quality_control_notes': 'Product recalled due to batch expiry. Awaiting disposal.',
                'regulatory_code': f'RECALL-CS-{batch.lot_number}-001'
            }
        ])
    
    # Vitamin D3 batches (quarantined batch)
    vitamin_batches = batches.filter(product__name__icontains="Vitamin")
    for batch in vitamin_batches[:1]:  # Take first vitamin batch
        sample_packs.extend([
            {
                'batch': batch,
                'serial_number': f'VIT-{batch.lot_number}-001',
                'pack_size': 60,
                'pack_type': 'bottle',
                'status': 'quarantined',
                'location': 'Quarantine Area',
                'warehouse_section': 'Q-01',
                'quality_control_passed': False,
                'quality_control_notes': 'Pack quarantined due to batch quality issues. Investigation ongoing.'
            }
        ])
    
    created_count = 0
    for pack_data in sample_packs:
        # Check if pack already exists
        if not Pack.objects.filter(serial_number=pack_data['serial_number']).exists():
            pack = Pack.objects.create(**pack_data)
            print(f"Created pack: {pack.serial_number} - {pack.batch.product.name}")
            created_count += 1
        else:
            print(f"Pack {pack_data['serial_number']} already exists, skipping...")
    
    print(f"\nCreated {created_count} new packs.")
    print(f"Total packs in database: {Pack.objects.count()}")

if __name__ == '__main__':
    create_sample_packs()
