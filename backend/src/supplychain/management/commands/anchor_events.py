"""
Management command to anchor events to blockchain.
"""

import contextlib
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from supplychain.models import Event
from supplychain.services.blockchain import blockchain_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Anchor pending events to blockchain"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10,
            help="Number of events to process in each batch",
        )
        parser.add_argument(
            "--max-age-hours",
            type=int,
            default=24,
            help="Maximum age of events to anchor (in hours)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be anchored without actually doing it",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force anchoring even for very recent events",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        max_age_hours = options["max_age_hours"]
        dry_run = options["dry_run"]
        force = options["force"]

        self.stdout.write("Starting blockchain anchoring process...")
        self.stdout.write(f"Batch size: {batch_size}")
        self.stdout.write(f"Max age: {max_age_hours} hours")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN MODE - No actual anchoring will be performed"
                )
            )

        # Find events that need anchoring
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)

        queryset = Event.objects.filter(
            integrity_status="pending", deleted_at__isnull=True
        )

        if not force:
            queryset = queryset.filter(created_at__lte=cutoff_time)

        pending_events = queryset.order_by("created_at")[:batch_size]

        if not pending_events:
            self.stdout.write(self.style.SUCCESS("No events found that need anchoring"))
            return

        self.stdout.write(f"Found {len(pending_events)} events to anchor")

        anchored_count = 0
        failed_count = 0

        for event in pending_events:
            try:
                if dry_run:
                    self.stdout.write(
                        f"Would anchor event {event.id}: {event.description[:50]}..."
                    )
                    continue

                # Ensure event has hash
                if not event.event_hash:
                    event.update_event_hash()

                # Anchor to blockchain
                result = blockchain_service.anchor_event(event)

                if result["success"]:
                    event.mark_blockchain_anchored(
                        result["tx_hash"], result["block_number"]
                    )
                    anchored_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Anchored event {event.id} - TX: {result['tx_hash']}"
                        )
                    )
                else:
                    event.mark_blockchain_failed()
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Failed to anchor event {event.id}: {result.get('error', 'Unknown error')}"
                        )
                    )

            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing event {event.id}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f"✗ Error processing event {event.id}: {str(e)}")
                )

                try:
                    event.mark_blockchain_failed()
                except Exception:
                    contextlib.suppress(
                        Exception
                    )  # Don't fail the entire process if we can't update status

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nCompleted anchoring process:\n"
                    f"  - Successfully anchored: {anchored_count}\n"
                    f"  - Failed: {failed_count}\n"
                    f"  - Total processed: {len(pending_events)}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nDry run completed - would have processed {len(pending_events)} events"
                )
            )
