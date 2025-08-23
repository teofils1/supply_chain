#!/usr/bin/env python3
"""
Script to create sample events for testing the event management feature.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone
import random

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from supplychain.models import Product, Batch, Pack, Shipment, Event
from django.contrib.auth import get_user_model

User = get_user_model()

def create_sample_events():
    """Create sample events for testing."""
    
    # Get existing entities
    products = list(Product.objects.all())
    batches = list(Batch.objects.all())
    packs = list(Pack.objects.all())
    shipments = list(Shipment.objects.all())
    users = list(User.objects.all())
    
    if not any([products, batches, packs, shipments]):
        print("No entities found. Please create products, batches, packs, and shipments first.")
        return
    
    # Sample locations
    locations = [
        'Warehouse A - Chicago, IL',
        'Manufacturing Plant - Boston, MA',
        'Distribution Center - Atlanta, GA',
        'Quality Control Lab - New York, NY',
        'Cold Storage Facility - Miami, FL',
        'Packaging Center - Dallas, TX',
        'Shipping Dock - Seattle, WA',
        'Receiving Bay - Denver, CO',
        'Temperature Controlled Room - Phoenix, AZ',
        'Clean Room - San Francisco, CA',
    ]
    
    # Sample IP addresses
    ip_addresses = [
        '192.168.1.100',
        '10.0.0.50',
        '172.16.0.25',
        '192.168.100.200',
        '10.1.1.75',
    ]
    
    # Sample user agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Supply Chain Management System v1.0',
        'Mobile App v2.1.0',
    ]
    
    sample_events = []
    
    # Product Events
    for product in products[:3]:  # Limit to first 3 products
        # Product created event
        sample_events.append({
            'event_type': 'created',
            'entity_type': 'product',
            'entity_id': product.id,
            'description': f'Product "{product.name}" was created in the system',
            'severity': 'info',
            'location': random.choice(locations),
            'user': random.choice(users) if users else None,
            'timestamp_offset': -random.randint(30, 90),  # 30-90 days ago
            'metadata': {
                'gtin': product.gtin,
                'form': product.form,
                'strength': product.strength,
                'action': 'product_registration'
            }
        })
        
        # Product updated event
        sample_events.append({
            'event_type': 'updated',
            'entity_type': 'product',
            'entity_id': product.id,
            'description': f'Product "{product.name}" information was updated',
            'severity': 'info',
            'location': random.choice(locations),
            'user': random.choice(users) if users else None,
            'timestamp_offset': -random.randint(5, 25),  # 5-25 days ago
            'metadata': {
                'fields_updated': ['storage_range', 'notes'],
                'action': 'product_update'
            }
        })
    
    # Batch Events
    for batch in batches[:4]:  # Limit to first 4 batches
        # Batch created event
        sample_events.append({
            'event_type': 'created',
            'entity_type': 'batch',
            'entity_id': batch.id,
            'description': f'Batch {batch.lot_number} was manufactured',
            'severity': 'info',
            'location': random.choice(locations),
            'user': random.choice(users) if users else None,
            'timestamp_offset': -random.randint(20, 60),  # 20-60 days ago
            'metadata': {
                'lot_number': batch.lot_number,
                'product_name': batch.product.name,
                'quantity_produced': batch.quantity_produced,
                'manufacturing_date': batch.manufacturing_date.isoformat() if batch.manufacturing_date else None,
                'action': 'batch_manufacturing'
            }
        })
        
        # Quality check event
        sample_events.append({
            'event_type': 'quality_check',
            'entity_type': 'batch',
            'entity_id': batch.id,
            'description': f'Quality control check completed for batch {batch.lot_number}',
            'severity': 'medium',
            'location': 'Quality Control Lab - New York, NY',
            'user': random.choice(users) if users else None,
            'timestamp_offset': -random.randint(15, 45),  # 15-45 days ago
            'metadata': {
                'test_results': {
                    'purity': '99.8%',
                    'potency': '101.2%',
                    'moisture': '0.3%',
                    'status': 'passed'
                },
                'inspector': 'QC Team',
                'action': 'quality_control'
            }
        })
        
        # Status change event
        if batch.status != 'active':
            sample_events.append({
                'event_type': 'status_changed',
                'entity_type': 'batch',
                'entity_id': batch.id,
                'description': f'Batch {batch.lot_number} status changed to {batch.status}',
                'severity': 'medium' if batch.status == 'quarantined' else 'info',
                'location': random.choice(locations),
                'user': random.choice(users) if users else None,
                'timestamp_offset': -random.randint(5, 20),  # 5-20 days ago
                'metadata': {
                    'old_status': 'active',
                    'new_status': batch.status,
                    'reason': 'Quality review' if batch.status == 'quarantined' else 'Standard process',
                    'action': 'status_update'
                }
            })
    
    # Pack Events
    for pack in packs[:5]:  # Limit to first 5 packs
        # Pack created event
        sample_events.append({
            'event_type': 'created',
            'entity_type': 'pack',
            'entity_id': pack.id,
            'description': f'Pack {pack.serial_number} was created from batch {pack.batch.lot_number}',
            'severity': 'info',
            'location': random.choice(locations),
            'user': random.choice(users) if users else None,
            'timestamp_offset': -random.randint(10, 30),  # 10-30 days ago
            'metadata': {
                'serial_number': pack.serial_number,
                'batch_lot_number': pack.batch.lot_number,
                'pack_size': pack.pack_size,
                'pack_type': pack.pack_type,
                'action': 'pack_creation'
            }
        })
        
        # Location change event
        sample_events.append({
            'event_type': 'location_changed',
            'entity_type': 'pack',
            'entity_id': pack.id,
            'description': f'Pack {pack.serial_number} moved to {pack.location}',
            'severity': 'info',
            'location': pack.location,
            'user': random.choice(users) if users else None,
            'timestamp_offset': -random.randint(3, 15),  # 3-15 days ago
            'metadata': {
                'old_location': random.choice(locations),
                'new_location': pack.location,
                'reason': 'Inventory reorganization',
                'action': 'location_update'
            }
        })
        
        # Temperature alert (for some packs)
        if random.choice([True, False]):
            sample_events.append({
                'event_type': 'temperature_alert',
                'entity_type': 'pack',
                'entity_id': pack.id,
                'description': f'Temperature excursion detected for pack {pack.serial_number}',
                'severity': 'high',
                'location': pack.location,
                'user': None,  # System generated
                'timestamp_offset': -random.randint(1, 7),  # 1-7 days ago
                'metadata': {
                    'temperature_recorded': 28.5,
                    'temperature_limit': 25.0,
                    'duration_minutes': 15,
                    'sensor_id': f'TEMP_{random.randint(100, 999)}',
                    'action': 'temperature_monitoring'
                }
            })
    
    # Shipment Events
    for shipment in shipments[:3]:  # Limit to first 3 shipments
        # Shipment created event
        sample_events.append({
            'event_type': 'created',
            'entity_type': 'shipment',
            'entity_id': shipment.id,
            'description': f'Shipment {shipment.tracking_number} was created',
            'severity': 'info',
            'location': shipment.origin_name,
            'user': random.choice(users) if users else None,
            'timestamp_offset': -random.randint(5, 15),  # 5-15 days ago
            'metadata': {
                'tracking_number': shipment.tracking_number,
                'carrier': shipment.carrier,
                'service_type': shipment.service_type,
                'pack_count': shipment.pack_count,
                'action': 'shipment_creation'
            }
        })
        
        # Shipment status changes
        status_progression = ['confirmed', 'picked_up', 'in_transit']
        if shipment.status in status_progression:
            for i, status in enumerate(status_progression):
                if status == shipment.status:
                    break
                sample_events.append({
                    'event_type': 'status_changed',
                    'entity_type': 'shipment',
                    'entity_id': shipment.id,
                    'description': f'Shipment {shipment.tracking_number} status changed to {status}',
                    'severity': 'info',
                    'location': shipment.origin_name if status == 'confirmed' else 'In Transit',
                    'user': random.choice(users) if users and status == 'confirmed' else None,
                    'timestamp_offset': -random.randint(3, 10) + i,  # Progressive timestamps
                    'metadata': {
                        'old_status': 'pending' if i == 0 else status_progression[i-1],
                        'new_status': status,
                        'carrier_update': True,
                        'action': 'status_update'
                    }
                })
        
        # Delivered event (for delivered shipments)
        if shipment.status == 'delivered':
            sample_events.append({
                'event_type': 'delivered',
                'entity_type': 'shipment',
                'entity_id': shipment.id,
                'description': f'Shipment {shipment.tracking_number} was delivered to {shipment.destination_name}',
                'severity': 'info',
                'location': shipment.destination_name,
                'user': None,  # System/carrier update
                'timestamp_offset': -random.randint(0, 3),  # 0-3 days ago
                'metadata': {
                    'delivery_time': (datetime.now() - timedelta(days=random.randint(0, 3))).isoformat(),
                    'recipient': 'Receiving Department',
                    'signature_required': True,
                    'action': 'delivery_confirmation'
                }
            })
    
    # System Events
    sample_events.extend([
        {
            'event_type': 'system_action',
            'entity_type': 'system',
            'entity_id': 1,
            'description': 'Daily inventory reconciliation completed',
            'severity': 'info',
            'location': 'Data Center',
            'user': None,
            'timestamp_offset': -1,  # Yesterday
            'metadata': {
                'records_processed': 1247,
                'discrepancies_found': 3,
                'action': 'inventory_reconciliation'
            }
        },
        {
            'event_type': 'alert',
            'entity_type': 'system',
            'entity_id': 1,
            'description': 'Low inventory alert for critical products',
            'severity': 'high',
            'location': 'Inventory Management System',
            'user': None,
            'timestamp_offset': -2,  # 2 days ago
            'metadata': {
                'products_affected': 5,
                'threshold_percentage': 10,
                'action': 'inventory_alert'
            }
        }
    ])
    
    # Create events in the database
    created_count = 0
    for event_data in sample_events:
        # Calculate timestamp
        timestamp = timezone.now() + timedelta(days=event_data.pop('timestamp_offset'))
        
        # Create the event
        event = Event.objects.create(
            event_type=event_data['event_type'],
            entity_type=event_data['entity_type'],
            entity_id=event_data['entity_id'],
            description=event_data['description'],
            severity=event_data['severity'],
            location=event_data['location'],
            user=event_data['user'],
            metadata=event_data['metadata'],
            ip_address=random.choice(ip_addresses),
            user_agent=random.choice(user_agents),
            system_info={
                'version': '1.0.0',
                'environment': 'development',
                'server': 'app-server-01'
            }
        )
        
        # Update the timestamp (since auto_now_add prevents setting it directly)
        Event.objects.filter(id=event.id).update(timestamp=timestamp)
        
        created_count += 1
        print(f"Created event: {event.event_type} - {event.entity_type}#{event.entity_id} ({event.severity})")
    
    print(f"\nCreated {created_count} sample events.")
    print(f"Total events in database: {Event.objects.count()}")

if __name__ == '__main__':
    create_sample_events()
