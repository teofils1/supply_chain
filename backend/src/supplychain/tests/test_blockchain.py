"""
Test blockchain anchoring functionality for events.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from supplychain.models import Event, Product
from supplychain.services.blockchain import blockchain_service

User = get_user_model()


class BlockchainAnchoringTestCase(TestCase):
    """Test blockchain anchoring functionality."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create test product for event
        self.product = Product.objects.create(
            name="Test Product",
            gtin="1234567890123",
            form="tablet",
            strength="10mg",
            status="active",
        )

    def test_event_hash_computation(self):
        """Test that event hashes are computed correctly."""
        event = Event.create_event(
            event_type="created",
            entity_type="product",
            entity_id=self.product.id,
            description="Test product created",
            user=self.user,
        )

        # Event should have a hash computed automatically
        self.assertIsNotNone(event.event_hash)
        self.assertEqual(len(event.event_hash), 64)  # SHA-256 hex string

        # Hash should be deterministic
        computed_hash = event.compute_event_hash()
        self.assertEqual(event.event_hash, computed_hash)

    def test_event_integrity_verification(self):
        """Test event integrity verification."""
        event = Event.create_event(
            event_type="created",
            entity_type="product",
            entity_id=self.product.id,
            description="Test product created",
            user=self.user,
        )

        # Initially, integrity should be verified
        self.assertTrue(event.verify_integrity())

        # If we manually change the stored hash, integrity should fail
        original_hash = event.event_hash
        event.event_hash = "tampered_hash"
        event.save(update_fields=["event_hash"])

        self.assertFalse(event.verify_integrity())

        # Restore original hash
        event.event_hash = original_hash
        event.save(update_fields=["event_hash"])
        self.assertTrue(event.verify_integrity())

    def test_blockchain_anchoring_mock(self):
        """Test mock blockchain anchoring."""
        event = Event.create_event(
            event_type="created",
            entity_type="product",
            entity_id=self.product.id,
            description="Test product created",
            user=self.user,
        )

        # Initially, event should not be anchored
        self.assertFalse(event.is_blockchain_anchored)
        self.assertEqual(event.integrity_status, "pending")

        # Anchor event to blockchain (mock)
        result = blockchain_service.anchor_event(event)

        self.assertTrue(result["success"])
        self.assertIsNotNone(result["tx_hash"])
        self.assertIsNotNone(result["block_number"])

        # Mark event as anchored
        event.mark_blockchain_anchored(result["tx_hash"], result["block_number"])

        # Event should now be anchored
        self.assertTrue(event.is_blockchain_anchored)
        self.assertEqual(event.integrity_status, "anchored")
        self.assertIsNotNone(event.blockchain_tx_hash)
        self.assertIsNotNone(event.blockchain_block_number)
        self.assertIsNotNone(event.blockchain_explorer_url)

    def test_blockchain_verification_mock(self):
        """Test mock blockchain verification."""
        event = Event.create_event(
            event_type="created",
            entity_type="product",
            entity_id=self.product.id,
            description="Test product created",
            user=self.user,
        )

        # Anchor event first
        anchor_result = blockchain_service.anchor_event(event)
        event.mark_blockchain_anchored(
            anchor_result["tx_hash"], anchor_result["block_number"]
        )

        # Verify anchored event
        verification = blockchain_service.verify_anchored_event(event)

        self.assertTrue(verification["verified"])
        self.assertTrue(verification["integrity_verified"])
        self.assertEqual(verification["tx_hash"], event.blockchain_tx_hash)
        self.assertEqual(verification["block_number"], event.blockchain_block_number)

    def test_event_hash_consistency(self):
        """Test that event hashes remain consistent across computations."""
        event = Event.create_event(
            event_type="quality_check",
            entity_type="product",
            entity_id=self.product.id,
            description="Quality check performed",
            user=self.user,
            severity="medium",
            location="Factory A",
            metadata={"temperature": 20.5, "humidity": 45, "batch_number": "B001"},
        )

        # Compute hash multiple times
        hash1 = event.compute_event_hash()
        hash2 = event.compute_event_hash()
        hash3 = event.compute_event_hash()

        # All hashes should be identical
        self.assertEqual(hash1, hash2)
        self.assertEqual(hash2, hash3)
        self.assertEqual(event.event_hash, hash1)

    def test_event_hash_changes_with_data(self):
        """Test that event hashes change when event data changes."""
        event = Event.create_event(
            event_type="created",
            entity_type="product",
            entity_id=self.product.id,
            description="Original description",
            user=self.user,
        )

        original_hash = event.event_hash

        # Change event description
        event.description = "Updated description"
        event.save()

        # Hash should be different now
        new_hash = event.compute_event_hash()
        self.assertNotEqual(original_hash, new_hash)

    def test_batch_anchoring_mock(self):
        """Test batch anchoring of multiple events."""
        events = []
        for i in range(3):
            event = Event.create_event(
                event_type="created",
                entity_type="product",
                entity_id=self.product.id,
                description=f"Test event {i}",
                user=self.user,
            )
            events.append(event)

        # Batch anchor events
        result = blockchain_service.batch_anchor_events(events)

        self.assertTrue(result["success"])
        self.assertEqual(result["batch_size"], 3)
        self.assertEqual(len(result["results"]), 3)

        # Check that all events were processed
        for event_result in result["results"]:
            self.assertIn("event_id", event_result)
            self.assertIn("result", event_result)
            self.assertTrue(event_result["result"]["success"])
