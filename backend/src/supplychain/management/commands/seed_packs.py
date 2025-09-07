"""
Django management command to seed packs data.

Usage:
    uv run python src/manage.py seed_packs
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import random
import string

import supplychain.models as m


class Command(BaseCommand):
    help = "Seed database with sample packs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing packs before seeding",
        )
        parser.add_argument(
            "--per-batch",
            type=int,
            default=5,
            help="Average number of packs per batch (default: 5)",
        )

    def generate_serial_number(self, batch, pack_type):
        """Generate a unique serial number for the pack."""
        # Format: GTIN-LOTNUM-PACKTYPE-XXXXX
        gtin_last4 = batch.product.gtin[-4:]
        lot_last3 = batch.lot_number[-3:] if len(batch.lot_number) >= 3 else batch.lot_number
        
        # Pack type abbreviations
        type_abbrev = {
            "bottle": "BTL",
            "box": "BOX", 
            "blister": "BLS",
            "vial": "VIA",
            "tube": "TUB",
            "sachet": "SAC",
            "ampoule": "AMP",
            "syringe": "SYR",
            "inhaler": "INH",
            "other": "OTH"
        }.get(pack_type, "OTH")
        
        # Generate unique suffix
        while True:
            suffix = ''.join(random.choices(string.digits, k=5))
            serial = f"{gtin_last4}{lot_last3}{type_abbrev}{suffix}"
            
            if not m.Pack.objects.filter(serial_number=serial).exists():
                return serial

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing packs...")
            m.Pack.objects.all().delete()

        # Check if batches exist
        batches = list(m.Batch.objects.all())
        if not batches:
            self.stdout.write(
                self.style.ERROR(
                    "No batches found. Please run 'python manage.py seed_batches' first."
                )
            )
            return

        self.stdout.write(f"Seeding packs for {len(batches)} batches...")

        # Pack type mapping based on product form
        form_to_pack_type = {
            "tablet": ["bottle", "blister", "box"],
            "capsule": ["bottle", "blister", "box"],
            "liquid": ["bottle", "vial"],
            "injection": ["vial", "ampoule", "syringe"],
            "cream": ["tube", "box"],
            "ointment": ["tube", "box"],
            "powder": ["bottle", "sachet", "box"],
            "other": ["box", "bottle"],
        }

        # Location data
        warehouses = [
            "Central Distribution Center - New York",
            "Regional Warehouse - Chicago",
            "Distribution Hub - Los Angeles", 
            "Medical Supply Center - Atlanta",
            "Pharmaceutical Depot - Boston",
            "Healthcare Distribution - Dallas",
            "Supply Chain Center - Seattle",
            "Regional Storage - Miami",
            "Distribution Facility - Denver",
            "Medical Warehouse - Phoenix",
        ]

        warehouse_sections = [
            "Section A - Temperature Controlled",
            "Section B - Ambient Storage",
            "Section C - Cold Storage",
            "Section D - Quarantine Area",
            "Section E - Staging Area",
            "Section F - High Value Items",
            "Section G - Bulk Storage",
            "Section H - Fast Moving Items",
        ]

        # Status distribution
        statuses = ["active", "shipped", "delivered", "quarantined", "damaged"]
        status_weights = [0.4, 0.25, 0.2, 0.1, 0.05]

        # Quality control notes
        qc_notes_templates = [
            "Pack integrity verified. All seals intact.",
            "Visual inspection passed. No damage noted.",
            "Pack meets all quality standards.",
            "Labeling and packaging correct.",
            "Temperature monitoring during storage confirmed.",
            "Pack ready for distribution.",
            "Quality control completed successfully.",
            "No deviations noted during inspection.",
        ]

        with transaction.atomic():
            packs_created = 0
            
            for batch in batches:
                # Determine pack type based on product form
                product_form = batch.product.form
                possible_pack_types = form_to_pack_type.get(product_form, ["box"])
                
                # Number of packs for this batch (Poisson-like distribution)
                num_packs = max(1, random.randint(1, options["per_batch"] * 2))
                
                for i in range(num_packs):
                    pack_type = random.choice(possible_pack_types)
                    serial_number = self.generate_serial_number(batch, pack_type)
                    
                    # Pack size varies by type and product
                    if product_form in ["injection", "liquid"]:
                        pack_size = random.choice([1, 5, 10, 20])  # Smaller packs for liquids
                    elif pack_type == "blister":
                        pack_size = random.choice([10, 14, 21, 28, 30])  # Blister standards
                    elif pack_type == "bottle":
                        pack_size = random.choice([30, 60, 90, 100, 120])  # Bottle standards
                    else:
                        pack_size = random.choice([1, 10, 25, 50, 100])
                    
                    # Determine status and related dates
                    status = random.choices(statuses, weights=status_weights)[0]
                    
                    shipped_date = None
                    delivered_date = None
                    tracking_number = ""
                    
                    if status in ["shipped", "delivered"]:
                        # Shipped 1-30 days ago
                        shipped_date = timezone.now() - timedelta(days=random.randint(1, 30))
                        tracking_number = f"TRK{random.randint(100000000, 999999999)}"
                        
                        if status == "delivered":
                            # Delivered 1-5 days after shipping
                            delivered_date = shipped_date + timedelta(days=random.randint(1, 5))
                    
                    # Quality control
                    quality_control_passed = status not in ["quarantined", "damaged"]
                    qc_notes = random.choice(qc_notes_templates)
                    
                    if status == "quarantined":
                        qc_notes = "Pack under investigation for potential quality issues."
                    elif status == "damaged":
                        qc_notes = "Pack damaged during handling. Requires assessment."
                    
                    # Location
                    location = random.choice(warehouses)
                    warehouse_section = random.choice(warehouse_sections)
                    
                    # Customer reference for shipped/delivered packs
                    customer_reference = ""
                    if status in ["shipped", "delivered"]:
                        customer_reference = f"CUST{random.randint(10000, 99999)}"
                    
                    pack_data = {
                        "batch": batch,
                        "serial_number": serial_number,
                        "pack_size": pack_size,
                        "pack_type": pack_type,
                        "status": status,
                        "location": location,
                        "warehouse_section": warehouse_section,
                        "quality_control_notes": qc_notes,
                        "quality_control_passed": quality_control_passed,
                        "regulatory_code": f"REG-{serial_number[-8:]}",
                        "customer_reference": customer_reference,
                        "shipped_date": shipped_date,
                        "delivered_date": delivered_date,
                        "tracking_number": tracking_number,
                    }
                    
                    try:
                        pack = m.Pack.objects.create(**pack_data)
                        packs_created += 1
                        
                        status_color = {
                            "active": self.style.SUCCESS,
                            "shipped": self.style.HTTP_INFO,
                            "delivered": self.style.SUCCESS,
                            "quarantined": self.style.WARNING,
                            "damaged": self.style.ERROR,
                        }.get(status, self.style.SUCCESS)
                        
                        if packs_created % 10 == 0 or packs_created <= 20:  # Show first 20 and every 10th
                            self.stdout.write(
                                status_color(
                                    f"Created pack: {pack.serial_number} - {pack.product_name} ({pack.status})"
                                )
                            )
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to create pack for batch {batch.lot_number}: {e}"
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {packs_created} packs")
        )
        
        # Summary statistics
        total_packs = m.Pack.objects.count()
        active_packs = m.Pack.objects.filter(status="active").count()
        shipped_packs = m.Pack.objects.filter(status="shipped").count()
        delivered_packs = m.Pack.objects.filter(status="delivered").count()
        quarantined_packs = m.Pack.objects.filter(status="quarantined").count()
        damaged_packs = m.Pack.objects.filter(status="damaged").count()
        
        self.stdout.write("\nPack Summary:")
        self.stdout.write(f"  Total packs: {total_packs}")
        self.stdout.write(f"  Active: {active_packs}")
        self.stdout.write(f"  Shipped: {shipped_packs}")
        self.stdout.write(f"  Delivered: {delivered_packs}")
        self.stdout.write(f"  Quarantined: {quarantined_packs}")
        self.stdout.write(f"  Damaged: {damaged_packs}")
        
        # Pack type distribution
        self.stdout.write("\nPack Types:")
        for pack_type_choice in m.Pack.PACK_TYPE_CHOICES:
            pack_type = pack_type_choice[0]
            count = m.Pack.objects.filter(pack_type=pack_type).count()
            if count > 0:
                self.stdout.write(f"  {pack_type_choice[1]}: {count}")
