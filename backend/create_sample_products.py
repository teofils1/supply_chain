#!/usr/bin/env python3
"""
Script to create sample products for testing the product view feature.
"""

import os
import sys
import django

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from supplychain.models import Product

def create_sample_products():
    """Create sample products for testing."""
    
    sample_products = [
        {
            'gtin': '12345678901234',
            'name': 'Aspirin 500mg Tablets',
            'description': 'Pain relief and anti-inflammatory medication',
            'form': 'tablet',
            'strength': '500mg',
            'storage_temp_min': 15.0,
            'storage_temp_max': 25.0,
            'storage_humidity_min': 30.0,
            'storage_humidity_max': 60.0,
            'manufacturer': 'PharmaCorp Inc.',
            'ndc': '12345-678',
            'status': 'active',
            'approval_number': 'FDA-2023-001'
        },
        {
            'gtin': '98765432109876',
            'name': 'Amoxicillin 250mg Capsules',
            'description': 'Antibiotic for bacterial infections',
            'form': 'capsule',
            'strength': '250mg',
            'storage_temp_min': 2.0,
            'storage_temp_max': 8.0,
            'storage_humidity_min': 40.0,
            'storage_humidity_max': 70.0,
            'manufacturer': 'MediLabs Ltd.',
            'ndc': '98765-432',
            'status': 'active',
            'approval_number': 'FDA-2023-002'
        },
        {
            'gtin': '11223344556677',
            'name': 'Insulin Injection 100IU/ml',
            'description': 'Fast-acting insulin for diabetes management',
            'form': 'injection',
            'strength': '100IU/ml',
            'storage_temp_min': 2.0,
            'storage_temp_max': 8.0,
            'manufacturer': 'BioPharm Solutions',
            'ndc': '11223-344',
            'status': 'active',
            'approval_number': 'FDA-2023-003'
        },
        {
            'gtin': '55667788990011',
            'name': 'Hydrocortisone Cream 1%',
            'description': 'Topical corticosteroid for skin inflammation',
            'form': 'cream',
            'strength': '1%',
            'storage_temp_min': 15.0,
            'storage_temp_max': 30.0,
            'manufacturer': 'DermaCare Inc.',
            'ndc': '55667-788',
            'status': 'active',
            'approval_number': 'FDA-2023-004'
        },
        {
            'gtin': '99887766554433',
            'name': 'Cough Syrup 120ml',
            'description': 'Liquid medication for cough relief',
            'form': 'liquid',
            'strength': '120ml',
            'storage_temp_min': 10.0,
            'storage_temp_max': 25.0,
            'manufacturer': 'CoughCare Pharmaceuticals',
            'ndc': '99887-766',
            'status': 'inactive',
            'approval_number': 'FDA-2022-005'
        },
        {
            'gtin': '13579246801357',
            'name': 'Vitamin D3 Powder 1000IU',
            'description': 'Vitamin D supplement in powder form',
            'form': 'powder',
            'strength': '1000IU',
            'storage_temp_min': 15.0,
            'storage_temp_max': 25.0,
            'storage_humidity_min': 20.0,
            'storage_humidity_max': 50.0,
            'manufacturer': 'VitaHealth Corp.',
            'ndc': '13579-246',
            'status': 'discontinued',
            'approval_number': 'FDA-2021-006'
        }
    ]
    
    created_count = 0
    for product_data in sample_products:
        # Check if product already exists
        if not Product.objects.filter(gtin=product_data['gtin']).exists():
            product = Product.objects.create(**product_data)
            print(f"Created product: {product.name} (GTIN: {product.gtin})")
            created_count += 1
        else:
            print(f"Product with GTIN {product_data['gtin']} already exists, skipping...")
    
    print(f"\nCreated {created_count} new products.")
    print(f"Total products in database: {Product.objects.count()}")

if __name__ == '__main__':
    create_sample_products()
