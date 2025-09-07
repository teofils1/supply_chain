"""
Management command to verify blockchain-anchored events.
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from supplychain.models import Event
from supplychain.services.blockchain import blockchain_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Verify blockchain-anchored events for integrity"

    def add_arguments(self, parser):
        parser.add_argument("--event-id", type=int, help="Verify specific event by ID")
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of events to verify in each batch",
        )
        parser.add_argument(
            "--days-back",
            type=int,
            default=7,
            help="How many days back to verify events",
        )
        parser.add_argument(
            "--fix-status",
            action="store_true",
            help="Fix integrity_status based on verification results",
        )

    def handle(self, *args, **options):
        event_id = options.get("event_id")
        batch_size = options["batch_size"]
        days_back = options["days_back"]
        fix_status = options["fix_status"]

        self.stdout.write("Starting event verification process...")

        if event_id:
            # Verify single event
            try:
                event = Event.objects.get(id=event_id)
                self.verify_single_event(event, fix_status)
            except Event.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Event {event_id} not found"))
                return
        else:
            # Verify batch of events
            cutoff_date = timezone.now() - timedelta(days=days_back)

            anchored_events = Event.objects.filter(
                integrity_status="anchored",
                blockchain_tx_hash__isnull=False,
                created_at__gte=cutoff_date,
                deleted_at__isnull=True,
            ).order_by("-created_at")[:batch_size]

            if not anchored_events:
                self.stdout.write(
                    self.style.SUCCESS("No anchored events found to verify")
                )
                return

            self.stdout.write(f"Verifying {len(anchored_events)} anchored events...")

            verified_count = 0
            failed_count = 0
            integrity_issues = 0

            for event in anchored_events:
                result = self.verify_single_event(event, fix_status, verbose=False)

                if result["verified"]:
                    verified_count += 1
                    if not result["integrity_verified"]:
                        integrity_issues += 1
                else:
                    failed_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nVerification completed:\n"
                    f"  - Blockchain verified: {verified_count}\n"
                    f"  - Verification failed: {failed_count}\n"
                    f"  - Integrity issues: {integrity_issues}\n"
                    f"  - Total checked: {len(anchored_events)}"
                )
            )

    def verify_single_event(self, event, fix_status=False, verbose=True):
        """Verify a single event and optionally fix its status."""
        try:
            if verbose:
                self.stdout.write(f"Verifying event {event.id}...")

            # Verify blockchain anchoring
            verification = blockchain_service.verify_anchored_event(event)

            # Check data integrity
            integrity_verified = event.verify_integrity()
            verification["integrity_verified"] = integrity_verified

            if verification["verified"]:
                if integrity_verified:
                    if verbose:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Event {event.id} - Blockchain verified, integrity intact"
                            )
                        )
                else:
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠ Event {event.id} - Blockchain verified, but data integrity compromised"
                            )
                        )
                        self.stdout.write(
                            f"  Stored hash: {verification['stored_hash']}"
                        )
                        self.stdout.write(
                            f"  Computed hash: {verification['computed_hash']}"
                        )
            else:
                if verbose:
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Event {event.id} - Blockchain verification failed: {verification.get('error', 'Unknown error')}"
                        )
                    )

                if fix_status:
                    event.mark_blockchain_failed()
                    if verbose:
                        self.stdout.write("  Status updated to 'failed'")

            return verification

        except Exception as e:
            if verbose:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error verifying event {event.id}: {str(e)}")
                )
            logger.error(f"Error verifying event {event.id}: {str(e)}")
            return {"verified": False, "error": str(e), "integrity_verified": False}
