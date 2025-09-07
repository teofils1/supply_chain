#!/usr/bin/env python
"""
Test script for blockchain anchoring functionality.
Run this from the backend directory with: uv run python test_blockchain_manual.py
"""

import os
import sys
import django

# Add the src directory to the Python path
sys.path.append('src')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from django.contrib.auth import get_user_model
from supplychain.models import Event, Product
from supplychain.services.blockchain import blockchain_service

User = get_user_model()

def test_blockchain_functionality():
    """Test blockchain anchoring functionality manually."""
    print("Testing blockchain anchoring functionality...")
    
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='test_blockchain_user',
            defaults={
                'email': 'test@blockchain.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        print(f"✓ Test user {'created' if created else 'found'}: {user.username}")
        
        # Get or create test product
        product, created = Product.objects.get_or_create(
            gtin='1234567890123',
            defaults={
                'name': 'Test Blockchain Product',
                'form': 'tablet',
                'strength': '10mg',
                'status': 'active'
            }
        )
        print(f"✓ Test product {'created' if created else 'found'}: {product.name}")
        
        # Create test event
        event = Event.create_event(
            event_type='created',
            entity_type='product',
            entity_id=product.id,
            description='Test product created for blockchain testing',
            user=user,
            severity='info',
            location='Test Lab',
            metadata={
                'test': True,
                'batch_number': 'TEST001',
                'temperature': 25.0
            }
        )
        print(f"✓ Event created: {event.id}")
        
        # Test event hash computation
        if event.event_hash:
            print(f"✓ Event hash computed: {event.event_hash[:16]}...")
        else:
            print("✗ Event hash not computed")
            return False
            
        # Test hash consistency
        hash1 = event.compute_event_hash()
        hash2 = event.compute_event_hash()
        if hash1 == hash2 == event.event_hash:
            print("✓ Event hash is consistent")
        else:
            print("✗ Event hash inconsistency detected")
            return False
            
        # Test integrity verification
        if event.verify_integrity():
            print("✓ Event integrity verified")
        else:
            print("✗ Event integrity verification failed")
            return False
            
        # Test blockchain anchoring (mock)
        print("\nTesting blockchain anchoring...")
        result = blockchain_service.anchor_event(event)
        
        if result['success']:
            print(f"✓ Blockchain anchoring successful")
            print(f"  TX Hash: {result['tx_hash']}")
            print(f"  Block Number: {result['block_number']}")
            
            # Mark event as anchored
            event.mark_blockchain_anchored(
                result['tx_hash'],
                result['block_number']
            )
            
            # Verify anchoring status
            if event.is_blockchain_anchored:
                print("✓ Event marked as blockchain anchored")
                print(f"  Status: {event.integrity_status}")
                print(f"  Explorer URL: {event.blockchain_explorer_url}")
            else:
                print("✗ Event not properly marked as anchored")
                return False
                
        else:
            print(f"✗ Blockchain anchoring failed: {result.get('error', 'Unknown error')}")
            return False
            
        # Test blockchain verification
        print("\nTesting blockchain verification...")
        verification = blockchain_service.verify_anchored_event(event)
        
        if verification['verified']:
            print("✓ Blockchain verification successful")
            print(f"  Integrity verified: {verification['integrity_verified']}")
            print(f"  Stored hash: {verification['stored_hash'][:16]}...")
            print(f"  Computed hash: {verification['computed_hash'][:16]}...")
        else:
            print(f"✗ Blockchain verification failed: {verification.get('error', 'Unknown error')}")
            return False
            
        # Test batch anchoring
        print("\nTesting batch anchoring...")
        events = []
        for i in range(3):
            batch_event = Event.create_event(
                event_type='quality_check',
                entity_type='product',
                entity_id=product.id,
                description=f'Batch test event {i+1}',
                user=user,
                metadata={'batch_test': True, 'index': i}
            )
            events.append(batch_event)
            
        batch_result = blockchain_service.batch_anchor_events(events)
        if batch_result['success']:
            print(f"✓ Batch anchoring successful for {batch_result['batch_size']} events")
            for result in batch_result['results']:
                if result['result']['success']:
                    print(f"  ✓ Event {result['event_id']} anchored")
                else:
                    print(f"  ✗ Event {result['event_id']} failed")
        else:
            print(f"✗ Batch anchoring failed: {batch_result.get('error', 'Unknown error')}")
            return False
            
        print("\n✅ All blockchain functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_blockchain_functionality()
    sys.exit(0 if success else 1)
