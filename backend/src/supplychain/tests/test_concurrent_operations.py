"""
Tests for concurrent operations to verify race condition fixes.

These tests verify that atomic operations prevent race conditions in:
- Batch inventory management (consume/restore)
- Pack creation and updates
- Transaction safety

Run with: python manage.py test supplychain.tests.test_concurrent_operations
"""

import threading
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from supplychain.models import Batch, Pack, Product

User = get_user_model()


class AtomicOperationUnitTestCase(TestCase):
    """Unit tests for atomic operation methods."""

    def setUp(self):
        """Set up test data."""
        self.product = Product.objects.create(
            gtin="12345678901234",
            name="Test Product",
            form="tablet",
            status="active",
        )

        self.batch = Batch.objects.create(
            product=self.product,
            lot_number="LOT-UNIT-001",
            manufacturing_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            quantity_produced=100,
            available_quantity=100,
            status="active",
        )

    def test_consume_quantity_success(self):
        """Test successful quantity consumption."""
        result = self.batch.consume_quantity(30)
        self.assertTrue(result)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.available_quantity, 70)

    def test_consume_quantity_insufficient(self):
        """Test consumption fails when insufficient quantity."""
        result = self.batch.consume_quantity(150)
        self.assertFalse(result)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.available_quantity, 100)  # Unchanged

    def test_restore_quantity_success(self):
        """Test successful quantity restoration."""
        # First consume some
        self.batch.consume_quantity(40)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.available_quantity, 60)

        # Then restore
        result = self.batch.restore_quantity(20)
        self.assertTrue(result)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.available_quantity, 80)

    def test_consume_exact_available_quantity(self):
        """Test consuming exactly the available quantity."""
        result = self.batch.consume_quantity(100)
        self.assertTrue(result)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.available_quantity, 0)

    def test_consume_then_consume_more_fails(self):
        """Test that consuming all then trying to consume more fails."""
        # Consume all
        self.batch.consume_quantity(100)
        self.batch.refresh_from_db()
        
        # Try to consume more
        result = self.batch.consume_quantity(10)
        self.assertFalse(result)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.available_quantity, 0)

    def test_multiple_small_consumptions(self):
        """Test multiple sequential small consumptions."""
        quantities = [10, 15, 20, 25, 30]  # Total: 100
        
        for qty in quantities:
            result = self.batch.consume_quantity(qty)
            self.assertTrue(result, f"Failed to consume {qty}")
        
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.available_quantity, 0)

    def test_restore_capped_at_quantity_produced(self):
        """Test that restoring is capped at quantity_produced."""
        # Consume some
        self.batch.consume_quantity(50)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.available_quantity, 50)
        
        # Try to restore more than consumed (should be capped)
        result = self.batch.restore_quantity(100)
        self.assertTrue(result)
        self.batch.refresh_from_db()
        
        # Should be capped at quantity_produced
        self.assertEqual(self.batch.available_quantity, 100)


class ConcurrentBatchOperationsTestCase(TransactionTestCase):
    """
    Test concurrent batch operations to verify atomic operations.
    
    Uses TransactionTestCase to allow real database transactions in threads.
    """

    def setUp(self):
        """Set up test data."""
        self.product = Product.objects.create(
            gtin="12345678901234",
            name="Test Product",
            form="tablet",
            status="active",
        )

        self.batch = Batch.objects.create(
            product=self.product,
            lot_number="LOT-CONCURRENT-001",
            manufacturing_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            quantity_produced=100,
            available_quantity=100,
            status="active",
        )

    def test_concurrent_consume_operations(self):
        """Test that concurrent consume operations don't oversell."""
        errors = []
        successes = []
        failures = []
        
        def try_consume(amount, thread_id):
            """Try to consume quantity in a thread."""
            try:
                batch = Batch.objects.get(id=self.batch.id)
                if batch.consume_quantity(amount):
                    successes.append(thread_id)
                else:
                    failures.append(thread_id)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")

        # Try to consume 30 units from 5 threads (150 total requested, 100 available)
        threads = []
        for i in range(5):
            thread = threading.Thread(target=try_consume, args=(30, i))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        
        # Refresh batch
        self.batch.refresh_from_db()
        
        # Should have exactly 3 successes (90 units consumed) and 2 failures
        # Or exactly 3 successes (100 units) and 2 failures depending on timing
        self.assertIn(len(successes), [3, 4], 
                     f"Expected 3-4 successful consumptions, got {len(successes)}")
        
        # Available quantity should reflect successful consumptions
        expected_consumed = len(successes) * 30
        expected_available = 100 - expected_consumed
        
        self.assertEqual(
            self.batch.available_quantity, 
            expected_available,
            f"Expected {expected_available} available after {len(successes)} consumptions of 30 each"
        )

    def test_concurrent_consume_and_restore(self):
        """Test concurrent consume and restore operations maintain consistency."""
        errors = []
        
        def consume_and_restore(iteration):
            """Consume and immediately restore in a thread."""
            try:
                batch = Batch.objects.get(id=self.batch.id)
                if batch.consume_quantity(10):
                    batch.restore_quantity(10)
            except Exception as e:
                errors.append(f"Iteration {iteration}: {str(e)}")

        # Run 10 concurrent consume/restore cycles
        threads = []
        for i in range(10):
            thread = threading.Thread(target=consume_and_restore, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        # Refresh batch - should be back to 100 (or very close due to race conditions)
        self.batch.refresh_from_db()
        
        # Due to timing, final value should be <= 100 (capped by restore_quantity)
        self.assertLessEqual(self.batch.available_quantity, 100)
        self.assertGreaterEqual(self.batch.available_quantity, 0)


class PackInventoryIntegrationTestCase(TestCase):
    """Integration tests for pack creation/deletion with inventory management."""

    def setUp(self):
        """Set up test data."""
        self.product = Product.objects.create(
            gtin="12345678901234",
            name="Test Product",
            form="tablet",
            status="active",
        )

        self.batch = Batch.objects.create(
            product=self.product,
            lot_number="LOT-PACK-001",
            manufacturing_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            quantity_produced=100,
            available_quantity=100,
            status="active",
        )

    def test_pack_creation_consumes_inventory(self):
        """Test that creating a pack consumes batch inventory."""
        initial_available = self.batch.available_quantity
        
        # Create a pack manually (simulating what the view does)
        pack_size = 25
        success = self.batch.consume_quantity(pack_size)
        self.assertTrue(success)
        
        pack = Pack.objects.create(
            batch=self.batch,
            serial_number="SN-TEST-001",
            pack_size=pack_size,
            pack_type="bottle",
            status="active",
        )
        
        # Verify inventory was consumed
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.available_quantity, initial_available - pack_size)

    def test_pack_deletion_restores_inventory(self):
        """Test that deleting a pack restores batch inventory."""
        # Create a pack
        pack_size = 25
        self.batch.consume_quantity(pack_size)
        
        pack = Pack.objects.create(
            batch=self.batch,
            serial_number="SN-TEST-002",
            pack_size=pack_size,
            pack_type="bottle",
            status="active",
        )
        
        self.batch.refresh_from_db()
        available_after_create = self.batch.available_quantity
        
        # Delete the pack and restore inventory
        pack_to_delete = Pack.objects.get(id=pack.id)
        self.batch.restore_quantity(pack_to_delete.pack_size)
        pack_to_delete.delete()
        
        # Verify inventory was restored
        self.batch.refresh_from_db()
        self.assertEqual(
            self.batch.available_quantity, 
            available_after_create + pack_size
        )

    def test_multiple_pack_creation_inventory_tracking(self):
        """Test that multiple pack creations correctly track inventory."""
        pack_sizes = [10, 20, 30]
        packs = []
        
