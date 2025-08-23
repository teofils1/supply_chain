#!/usr/bin/env python3
"""
Script to create sample batches for testing the batch view feature.
"""

import os
import sys
import django
from datetime import date, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from supplychain.models import Product, Batch

def create_sample_batches():
    """Create sample batches for testing."""
    
    # Get existing products
    products = Product.objects.all()
    if not products.exists():
        print("No products found. Please create products first.")
        return
    
    sample_batches = []
    
    # Aspirin 500mg Tablets
    aspirin = products.filter(name__icontains="Aspirin").first()
    if aspirin:
        sample_batches.extend([
            {
                'product': aspirin,
                'lot_number': 'ASP-2024-001',
                'manufacturing_date': date.today() - timedelta(days=30),
                'expiry_date': date.today() + timedelta(days=700),
                'quantity_produced': 10000,
                'manufacturing_location': 'New York, USA',
                'manufacturing_facility': 'PharmaCorp Manufacturing Plant A',
                'status': 'active',
                'quality_control_passed': True,
                'batch_size': '10,000 tablets',
                'quality_control_notes': 'All quality tests passed. Batch meets specifications.',
                'regulatory_approval_number': 'FDA-ASP-2024-001'
            },
            {
                'product': aspirin,
                'lot_number': 'ASP-2024-002',
                'manufacturing_date': date.today() - timedelta(days=15),
                'expiry_date': date.today() + timedelta(days=715),
                'quantity_produced': 15000,
                'manufacturing_location': 'New York, USA',
                'manufacturing_facility': 'PharmaCorp Manufacturing Plant A',
                'status': 'active',
                'quality_control_passed': True,
                'batch_size': '15,000 tablets',
                'quality_control_notes': 'Excellent quality batch. All parameters within limits.'
            }
        ])
    
    # Amoxicillin 250mg Capsules
    amoxicillin = products.filter(name__icontains="Amoxicillin").first()
    if amoxicillin:
        sample_batches.extend([
            {
                'product': amoxicillin,
                'lot_number': 'AMX-2024-001',
                'manufacturing_date': date.today() - timedelta(days=45),
                'expiry_date': date.today() + timedelta(days=545),
                'quantity_produced': 5000,
                'manufacturing_location': 'London, UK',
                'manufacturing_facility': 'MediLabs Production Facility',
                'status': 'active',
                'quality_control_passed': True,
                'batch_size': '5,000 capsules',
                'quality_control_notes': 'Batch passed all microbiological tests.',
                'certificate_of_analysis': 'COA-AMX-2024-001'
            },
            {
                'product': amoxicillin,
                'lot_number': 'AMX-2024-002',
                'manufacturing_date': date.today() - timedelta(days=60),
                'expiry_date': date.today() + timedelta(days=30),  # Expiring soon
                'quantity_produced': 3000,
                'manufacturing_location': 'London, UK',
                'manufacturing_facility': 'MediLabs Production Facility',
                'status': 'active',
                'quality_control_passed': True,
                'batch_size': '3,000 capsules',
                'quality_control_notes': 'Batch expiring soon. Priority for distribution.'
            }
        ])
    
    # Insulin Injection
    insulin = products.filter(name__icontains="Insulin").first()
    if insulin:
        sample_batches.extend([
            {
                'product': insulin,
                'lot_number': 'INS-2024-001',
                'manufacturing_date': date.today() - timedelta(days=20),
                'expiry_date': date.today() + timedelta(days=345),
                'quantity_produced': 1000,
                'manufacturing_location': 'Basel, Switzerland',
                'manufacturing_facility': 'BioPharm Cold Storage Facility',
                'status': 'active',
                'quality_control_passed': True,
                'batch_size': '1,000 vials',
                'quality_control_notes': 'Cold chain maintained throughout production.',
                'regulatory_approval_number': 'EMA-INS-2024-001'
            }
        ])
    
    # Hydrocortisone Cream
    hydrocortisone = products.filter(name__icontains="Hydrocortisone").first()
    if hydrocortisone:
        sample_batches.extend([
            {
                'product': hydrocortisone,
                'lot_number': 'HYD-2024-001',
                'manufacturing_date': date.today() - timedelta(days=90),
                'expiry_date': date.today() + timedelta(days=275),
                'quantity_produced': 2500,
                'manufacturing_location': 'Chicago, USA',
                'manufacturing_facility': 'DermaCare Topical Manufacturing',
                'status': 'active',
                'quality_control_passed': True,
                'batch_size': '2,500 tubes',
                'quality_control_notes': 'Viscosity and pH within acceptable range.'
            }
        ])
    
    # Cough Syrup (inactive product)
    cough_syrup = products.filter(name__icontains="Cough").first()
    if cough_syrup:
        sample_batches.extend([
            {
                'product': cough_syrup,
                'lot_number': 'CS-2023-001',
                'manufacturing_date': date.today() - timedelta(days=200),
                'expiry_date': date.today() - timedelta(days=50),  # Expired
                'quantity_produced': 1500,
                'manufacturing_location': 'Toronto, Canada',
                'manufacturing_facility': 'CoughCare Liquid Manufacturing',
                'status': 'expired',
                'quality_control_passed': True,
                'batch_size': '1,500 bottles',
                'quality_control_notes': 'Batch has expired. Awaiting disposal.'
            }
        ])
    
    # Vitamin D3 Powder (discontinued product)
    vitamin_d = products.filter(name__icontains="Vitamin").first()
    if vitamin_d:
        sample_batches.extend([
            {
                'product': vitamin_d,
                'lot_number': 'VIT-2023-001',
                'manufacturing_date': date.today() - timedelta(days=150),
                'expiry_date': date.today() + timedelta(days=200),
                'quantity_produced': 500,
                'manufacturing_location': 'San Diego, USA',
                'manufacturing_facility': 'VitaHealth Powder Processing',
                'status': 'quarantined',
                'quality_control_passed': False,
                'batch_size': '500 containers',
                'quality_control_notes': 'Failed moisture content test. Batch quarantined for investigation.',
                'supplier_batch_number': 'VH-VIT-2023-001'
            }
        ])
    
    created_count = 0
    for batch_data in sample_batches:
        # Check if batch already exists
        if not Batch.objects.filter(
            product=batch_data['product'], 
            lot_number=batch_data['lot_number']
        ).exists():
            batch = Batch.objects.create(**batch_data)
            print(f"Created batch: {batch.product.name} - Lot {batch.lot_number}")
            created_count += 1
        else:
            print(f"Batch {batch_data['lot_number']} for {batch_data['product'].name} already exists, skipping...")
    
    print(f"\nCreated {created_count} new batches.")
    print(f"Total batches in database: {Batch.objects.count()}")

if __name__ == '__main__':
    create_sample_batches()
