"""
Django management command to seed shipments data.

Usage:
    uv run python src/manage.py seed_shipments
"""

import random
import string
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

import supplychain.models as m


class Command(BaseCommand):
    help = "Seed database with sample shipments"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing shipments before seeding",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=20,
            help="Number of shipments to create (default: 20)",
        )

    def generate_tracking_number(self, carrier):
        """Generate a realistic tracking number based on carrier."""
        if carrier == "fedex":
            return f"FX{random.randint(100000000000, 999999999999)}"
        elif carrier == "ups":
            return f"1Z{random.choice(['123', '456', '789'])}{''.join(random.choices(string.ascii_uppercase + string.digits, k=11))}"
        elif carrier == "dhl":
            return f"DH{random.randint(1000000000, 9999999999)}"
        elif carrier == "usps":
            return f"US{random.randint(100000000000, 999999999999)}"
        elif carrier == "amazon":
            return f"TBA{random.randint(100000000, 999999999)}"
        else:
            return f"TRK{random.randint(100000000000, 999999999999)}"

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing shipments...")
            m.Shipment.objects.all().delete()

        # Check if packs exist
        packs = list(
            m.Pack.objects.filter(status__in=["active", "shipped", "delivered"])
        )
        if not packs:
            self.stdout.write(
                self.style.ERROR(
                    "No available packs found. Please run 'python manage.py seed_packs' first."
                )
            )
            return

        self.stdout.write(
            f"Seeding {options['count']} shipments from {len(packs)} available packs..."
        )

        # Address data
        origins = [
            {
                "name": "PharmaCorp Distribution Center",
                "address_line1": "123 Industrial Blvd",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "USA",
            },
            {
                "name": "MediLife Manufacturing",
                "address_line1": "456 Pharma Way",
                "city": "Chicago",
                "state": "IL",
                "postal_code": "60601",
                "country": "USA",
            },
            {
                "name": "Healthcare Solutions Warehouse",
                "address_line1": "789 Medical Drive",
                "city": "Los Angeles",
                "state": "CA",
                "postal_code": "90001",
                "country": "USA",
            },
            {
                "name": "Global Pharma Hub",
                "address_line1": "321 Supply Chain Rd",
                "city": "Atlanta",
                "state": "GA",
                "postal_code": "30301",
                "country": "USA",
            },
            {
                "name": "Northern Distribution",
                "address_line1": "654 Logistics Ave",
                "city": "Boston",
                "state": "MA",
                "postal_code": "02101",
                "country": "USA",
            },
        ]

        destinations = [
            {
                "name": "City General Hospital",
                "address_line1": "100 Hospital Drive",
                "city": "Miami",
                "state": "FL",
                "postal_code": "33101",
                "country": "USA",
            },
            {
                "name": "Regional Medical Center",
                "address_line1": "200 Healthcare Blvd",
                "city": "Dallas",
                "state": "TX",
                "postal_code": "75201",
                "country": "USA",
            },
            {
                "name": "Metro Pharmacy Chain",
                "address_line1": "300 Retail Plaza",
                "city": "Seattle",
                "state": "WA",
                "postal_code": "98101",
                "country": "USA",
            },
            {
                "name": "University Medical Center",
                "address_line1": "400 University Ave",
                "city": "Denver",
                "state": "CO",
                "postal_code": "80201",
                "country": "USA",
            },
            {
                "name": "Community Health Network",
                "address_line1": "500 Community Way",
                "city": "Phoenix",
                "state": "AZ",
                "postal_code": "85001",
                "country": "USA",
            },
            {
                "name": "Central Pharmacy",
                "address_line1": "600 Main Street",
                "city": "Kansas City",
                "state": "MO",
                "postal_code": "64101",
                "country": "USA",
            },
            {
                "name": "Coastal Medical Supply",
                "address_line1": "700 Ocean View Dr",
                "city": "San Diego",
                "state": "CA",
                "postal_code": "92101",
                "country": "USA",
            },
        ]

        # Status distribution (weighted)
        statuses = [
            "pending",
            "confirmed",
            "picked_up",
            "in_transit",
            "out_for_delivery",
            "delivered",
            "returned",
        ]
        status_weights = [0.1, 0.15, 0.1, 0.25, 0.15, 0.2, 0.05]

        # Carrier distribution
        carriers = ["fedex", "ups", "dhl", "usps", "amazon", "local", "internal"]
        carrier_weights = [0.25, 0.25, 0.15, 0.15, 0.1, 0.05, 0.05]

        # Service types
        service_types = [
            "standard",
            "express",
            "overnight",
            "ground",
            "air",
            "cold_chain",
        ]
        service_weights = [0.4, 0.2, 0.1, 0.15, 0.1, 0.05]

        # Temperature requirements
        temp_requirements = ["ambient", "cool", "frozen", "controlled"]
        temp_weights = [0.6, 0.25, 0.1, 0.05]

        with transaction.atomic():
            shipments_created = 0
            available_packs = packs.copy()

            for i in range(options["count"]):
                if not available_packs:
                    self.stdout.write(
                        self.style.WARNING("No more available packs for shipments")
                    )
                    break

                # Select carrier and generate tracking number
                carrier = random.choices(carriers, weights=carrier_weights)[0]
                tracking_number = self.generate_tracking_number(carrier)

                # Ensure unique tracking number
                while m.Shipment.objects.filter(
                    tracking_number=tracking_number
                ).exists():
                    tracking_number = self.generate_tracking_number(carrier)

                # Select addresses
                origin = random.choice(origins)
                destination = random.choice(destinations)

                # Determine status and related dates
                status = random.choices(statuses, weights=status_weights)[0]
                service_type = random.choices(service_types, weights=service_weights)[0]
                temp_requirement = random.choices(
                    temp_requirements, weights=temp_weights
                )[0]

                # Date logic based on status
                shipped_date = None
                estimated_delivery_date = None
                actual_delivery_date = None

                if status in ["picked_up", "in_transit", "out_for_delivery"]:
                    # Shipped 1-14 days ago
                    shipped_date = timezone.now() - timedelta(
                        days=random.randint(1, 14)
                    )
                    # Estimated delivery 2-7 days after shipping
                    estimated_delivery_date = shipped_date + timedelta(
                        days=random.randint(2, 7)
                    )

                elif status == "delivered":
                    # For delivered shipments, work backwards from delivery
                    # Delivered 1-10 days ago
                    actual_delivery_date = timezone.now() - timedelta(
                        days=random.randint(1, 10)
                    )
                    # Shipped 3-7 days before delivery
                    shipped_date = actual_delivery_date - timedelta(
                        days=random.randint(3, 7)
                    )
                    # Estimated was between shipped and delivered
                    est_days = (actual_delivery_date - shipped_date).days
                    if est_days > 1:
                        estimated_delivery_date = shipped_date + timedelta(
                            days=random.randint(1, est_days)
                        )
                    else:
                        estimated_delivery_date = shipped_date + timedelta(days=1)

                elif status == "returned":
                    # Similar to delivered but different final status
                    actual_delivery_date = timezone.now() - timedelta(
                        days=random.randint(1, 10)
                    )
                    shipped_date = actual_delivery_date - timedelta(
                        days=random.randint(3, 7)
                    )
                    est_days = (actual_delivery_date - shipped_date).days
                    if est_days > 1:
                        estimated_delivery_date = shipped_date + timedelta(
                            days=random.randint(1, est_days)
                        )
                    else:
                        estimated_delivery_date = shipped_date + timedelta(days=1)

                elif status in ["confirmed", "pending"]:
                    # Future estimated delivery
                    estimated_delivery_date = timezone.now() + timedelta(
                        days=random.randint(1, 10)
                    )

                # Special handling and instructions
                special_handling = (
                    random.choice([True, False])
                    if temp_requirement != "ambient"
                    else False
                )
                special_instructions = ""
                if special_handling:
                    instructions = [
                        "Handle with care - fragile medical supplies",
                        "Temperature monitoring required",
                        "Do not stack - sensitive packaging",
                        "Expedited delivery required",
                        "Signature required upon delivery",
                        "Cold chain integrity must be maintained",
                    ]
                    special_instructions = random.choice(instructions)

                # Shipping cost (varies by service type and distance)
                base_cost = Decimal("25.00")
                if service_type == "express":
                    shipping_cost = base_cost * Decimal("1.5")
                elif service_type == "overnight":
                    shipping_cost = base_cost * Decimal("2.0")
                elif service_type == "cold_chain":
                    shipping_cost = base_cost * Decimal("2.5")
                else:
                    shipping_cost = base_cost

                # Add random variation
                shipping_cost *= Decimal(str(random.uniform(0.8, 1.5)))
                shipping_cost = shipping_cost.quantize(Decimal("0.01"))

                # Notes
                notes_options = [
                    "Standard pharmaceutical shipment",
                    "Priority delivery requested",
                    "Customer requires tracking updates",
                    "Consolidation shipment",
                    "Return shipment processing",
                    "Quality control verified before shipping",
                    "Special packaging requirements met",
                ]
                notes = (
                    random.choice(notes_options) if random.choice([True, False]) else ""
                )

                shipment_data = {
                    "tracking_number": tracking_number,
                    "status": status,
                    "carrier": carrier,
                    "service_type": service_type,
                    # Origin
                    "origin_name": origin["name"],
                    "origin_address_line1": origin["address_line1"],
                    "origin_city": origin["city"],
                    "origin_state": origin["state"],
                    "origin_postal_code": origin["postal_code"],
                    "origin_country": origin["country"],
                    # Destination
                    "destination_name": destination["name"],
                    "destination_address_line1": destination["address_line1"],
                    "destination_city": destination["city"],
                    "destination_state": destination["state"],
                    "destination_postal_code": destination["postal_code"],
                    "destination_country": destination["country"],
                    # Dates
                    "shipped_date": shipped_date,
                    "estimated_delivery_date": estimated_delivery_date,
                    "actual_delivery_date": actual_delivery_date,
                    # Requirements
                    "temperature_requirement": temp_requirement,
                    "special_handling_required": special_handling,
                    "special_instructions": special_instructions,
                    # Cost
                    "shipping_cost": shipping_cost,
                    "currency": "USD",
                    "billing_reference": f"BILL-{random.randint(100000, 999999)}",
                    # Additional
                    "notes": notes,
                    "external_tracking_url": f"https://track.{carrier}.com/{tracking_number}",
                }

                try:
                    shipment = m.Shipment.objects.create(**shipment_data)

                    # Add packs to shipment (1-5 packs per shipment)
                    num_packs = min(random.randint(1, 5), len(available_packs))
                    selected_packs = random.sample(available_packs, num_packs)

                    for pack in selected_packs:
                        m.ShipmentPack.objects.create(
                            shipment=shipment,
                            pack=pack,
                            quantity_shipped=1,
                            notes=f"Pack {pack.serial_number} added to shipment",
                        )
                        available_packs.remove(pack)

                    shipments_created += 1

                    status_color = {
                        "pending": self.style.WARNING,
                        "confirmed": self.style.HTTP_INFO,
                        "picked_up": self.style.HTTP_INFO,
                        "in_transit": self.style.HTTP_INFO,
                        "out_for_delivery": self.style.HTTP_INFO,
                        "delivered": self.style.SUCCESS,
                        "returned": self.style.ERROR,
                    }.get(status, self.style.SUCCESS)

                    if (
                        shipments_created <= 10 or shipments_created % 5 == 0
                    ):  # Show first 10 and every 5th
                        self.stdout.write(
                            status_color(
                                f"Created shipment: {shipment.tracking_number} - {shipment.status} ({num_packs} packs)"
                            )
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to create shipment {tracking_number}: {e}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {shipments_created} shipments")
        )

        # Summary statistics
        total_shipments = m.Shipment.objects.count()
        self.stdout.write("\nShipment Summary:")
        self.stdout.write(f"  Total shipments: {total_shipments}")

        for status_choice in m.Shipment.STATUS_CHOICES:
            status = status_choice[0]
            count = m.Shipment.objects.filter(status=status).count()
            if count > 0:
                self.stdout.write(f"  {status_choice[1]}: {count}")

        # Carrier distribution
        self.stdout.write("\nCarrier Distribution:")
        for carrier_choice in m.Shipment.CARRIER_CHOICES:
            carrier = carrier_choice[0]
            count = m.Shipment.objects.filter(carrier=carrier).count()
            if count > 0:
                self.stdout.write(f"  {carrier_choice[1]}: {count}")

        # Total packs shipped
        total_pack_shipments = m.ShipmentPack.objects.count()
        self.stdout.write(
            f"\nTotal pack-shipment relationships: {total_pack_shipments}"
        )
