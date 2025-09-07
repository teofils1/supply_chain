"""
Django management command to seed batches data.

Usage:
    uv run python src/manage.py seed_batches
"""

import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

import supplychain.models as m


class Command(BaseCommand):
    help = "Seed database with sample batches"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing batches before seeding",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=30,
            help="Number of batches to create (default: 30)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing batches...")
            m.Batch.objects.all().delete()

        # Check if products exist
        products = list(m.Product.objects.all())
        if not products:
            self.stdout.write(
                self.style.ERROR(
                    "No products found. Please run 'python manage.py seed_products' first."
                )
            )
            return

        self.stdout.write(f"Seeding {options['count']} batches...")

        # Manufacturing locations and facilities
        locations = [
            "New York, NY, USA",
            "San Francisco, CA, USA",
            "Chicago, IL, USA",
            "Boston, MA, USA",
            "Atlanta, GA, USA",
            "London, UK",
            "Frankfurt, Germany",
            "Paris, France",
            "Tokyo, Japan",
            "Singapore",
            "Mumbai, India",
            "São Paulo, Brazil",
        ]

        facilities = [
            "Main Manufacturing Plant",
            "Advanced Production Facility",
            "Quality Assurance Center",
            "Primary Manufacturing Site",
            "Secondary Production Unit",
            "Specialized Manufacturing Hub",
            "Central Production Facility",
            "Regional Manufacturing Center",
        ]

        statuses = ["active", "released", "quarantined", "expired"]
        status_weights = [0.6, 0.25, 0.1, 0.05]  # Most batches are active

        # Quality control notes templates
        qc_notes_templates = [
            "All quality parameters within acceptable limits.",
            "Batch passed all required tests. No deviations noted.",
            "Minor deviation in appearance corrected during production.",
            "Stability testing in progress. Initial results satisfactory.",
            "Batch meets all regulatory requirements.",
            "Quality control completed successfully.",
            "All critical quality attributes verified.",
            "Batch released after thorough quality assessment.",
        ]

        with transaction.atomic():
            batches_created = 0

            for i in range(options["count"]):
                # Select random product
                product = random.choice(products)

                # Generate lot number (format: YYMMDDxxx where xxx is sequential)
                base_date = datetime.now() - timedelta(days=random.randint(30, 365))
                lot_number = f"{base_date.strftime('%y%m%d')}{random.randint(100, 999)}"

                # Check if this lot number already exists for this product
                if m.Batch.objects.filter(
                    product=product, lot_number=lot_number
                ).exists():
                    continue

                # Manufacturing date (30-365 days ago)
                manufacturing_date = base_date.date()

                # Expiry date (1-3 years from manufacturing)
                expiry_months = random.randint(12, 36)
                expiry_date = manufacturing_date + timedelta(days=expiry_months * 30)

                # Determine status based on expiry
                today = timezone.now().date()
                if expiry_date < today:
                    status = "expired"
                else:
                    status = random.choices(statuses[:-1], weights=status_weights[:-1])[
                        0
                    ]

                # Quantity produced (varies by product type)
                base_quantity = random.randint(1000, 10000)
                if product.form in ["injection", "liquid"]:
                    quantity_produced = random.randint(
                        500, 5000
                    )  # Smaller batches for liquids
                else:
                    quantity_produced = base_quantity

                # Quality control
                quality_control_passed = status != "quarantined"
                qc_notes = random.choice(qc_notes_templates)
                if status == "quarantined":
                    qc_notes = "Batch under investigation for potential quality issues."

                batch_data = {
                    "product": product,
                    "lot_number": lot_number,
                    "manufacturing_date": manufacturing_date,
                    "expiry_date": expiry_date,
                    "quantity_produced": quantity_produced,
                    "manufacturing_location": random.choice(locations),
                    "manufacturing_facility": random.choice(facilities),
                    "status": status,
                    "quality_control_notes": qc_notes,
                    "quality_control_passed": quality_control_passed,
                    "batch_size": f"{quantity_produced} units",
                    "supplier_batch_number": f"SUP-{lot_number}",
                    "regulatory_approval_number": f"REG-{product.gtin[-6:]}-{lot_number[-3:]}",
                    "certificate_of_analysis": f"COA-{lot_number}-{manufacturing_date.strftime('%Y%m%d')}",
                }

                try:
                    batch = m.Batch.objects.create(**batch_data)
                    batches_created += 1

                    status_color = {
                        "active": self.style.SUCCESS,
                        "released": self.style.SUCCESS,
                        "quarantined": self.style.WARNING,
                        "expired": self.style.ERROR,
                    }.get(status, self.style.SUCCESS)

                    self.stdout.write(
                        status_color(
                            f"Created batch: {batch.product.name} - Lot {batch.lot_number} ({batch.status})"
                        )
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to create batch for {product.name}: {e}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {batches_created} batches")
        )

        # Summary statistics
        total_batches = m.Batch.objects.count()
        active_batches = m.Batch.objects.filter(status="active").count()
        expired_batches = m.Batch.objects.filter(status="expired").count()
        quarantined_batches = m.Batch.objects.filter(status="quarantined").count()

        self.stdout.write("\nBatch Summary:")
        self.stdout.write(f"  Total batches: {total_batches}")
        self.stdout.write(f"  Active: {active_batches}")
        self.stdout.write(
            f"  Released: {m.Batch.objects.filter(status='released').count()}"
        )
        self.stdout.write(f"  Quarantined: {quarantined_batches}")
        self.stdout.write(f"  Expired: {expired_batches}")
