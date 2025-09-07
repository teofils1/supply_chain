"""
Django management command to seed products data.

Usage:
    uv run python src/manage.py seed_products
"""

from django.core.management.base import BaseCommand
from django.db import transaction

import supplychain.models as m


class Command(BaseCommand):
    help = "Seed database with sample products"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing products before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing products...")
            m.Product.objects.all().delete()

        self.stdout.write("Seeding products...")

        products_data = [
            {
                "gtin": "00123456789012",
                "name": "Aspirin 325mg",
                "description": "Pain relief and fever reducer tablets",
                "form": "tablet",
                "strength": "325mg",
                "storage_temp_min": 15.0,
                "storage_temp_max": 25.0,
                "storage_humidity_min": 30.0,
                "storage_humidity_max": 60.0,
                "manufacturer": "PharmaCorp Inc.",
                "ndc": "12345-123-12",
                "status": "active",
                "approval_number": "NDA123456",
            },
            {
                "gtin": "00123456789013",
                "name": "Amoxicillin 500mg",
                "description": "Antibiotic capsules for bacterial infections",
                "form": "capsule",
                "strength": "500mg",
                "storage_temp_min": 2.0,
                "storage_temp_max": 8.0,
                "storage_humidity_min": 40.0,
                "storage_humidity_max": 70.0,
                "manufacturer": "MediLife Labs",
                "ndc": "23456-234-23",
                "status": "active",
                "approval_number": "NDA234567",
            },
            {
                "gtin": "00123456789014",
                "name": "Insulin Glargine 100 units/mL",
                "description": "Long-acting insulin injection for diabetes",
                "form": "injection",
                "strength": "100 units/mL",
                "storage_temp_min": 2.0,
                "storage_temp_max": 8.0,
                "storage_humidity_min": 35.0,
                "storage_humidity_max": 65.0,
                "manufacturer": "DiabetesCare Pharma",
                "ndc": "34567-345-34",
                "status": "active",
                "approval_number": "NDA345678",
            },
            {
                "gtin": "00123456789015",
                "name": "Hydrocortisone Cream 1%",
                "description": "Topical anti-inflammatory cream",
                "form": "cream",
                "strength": "1%",
                "storage_temp_min": 15.0,
                "storage_temp_max": 30.0,
                "storage_humidity_min": 25.0,
                "storage_humidity_max": 55.0,
                "manufacturer": "SkinCare Solutions",
                "ndc": "45678-456-45",
                "status": "active",
                "approval_number": "NDA456789",
            },
            {
                "gtin": "00123456789016",
                "name": "Acetaminophen Liquid 160mg/5mL",
                "description": "Children's pain and fever reducer",
                "form": "liquid",
                "strength": "160mg/5mL",
                "storage_temp_min": 20.0,
                "storage_temp_max": 25.0,
                "storage_humidity_min": 30.0,
                "storage_humidity_max": 60.0,
                "manufacturer": "KidsHealth Pharma",
                "ndc": "56789-567-56",
                "status": "active",
                "approval_number": "NDA567890",
            },
            {
                "gtin": "00123456789017",
                "name": "Metformin HCl 850mg",
                "description": "Type 2 diabetes medication",
                "form": "tablet",
                "strength": "850mg",
                "storage_temp_min": 15.0,
                "storage_temp_max": 30.0,
                "storage_humidity_min": 35.0,
                "storage_humidity_max": 65.0,
                "manufacturer": "EndoCare Pharmaceuticals",
                "ndc": "67890-678-67",
                "status": "active",
                "approval_number": "NDA678901",
            },
            {
                "gtin": "00123456789018",
                "name": "Omeprazole 20mg",
                "description": "Proton pump inhibitor for acid reflux",
                "form": "capsule",
                "strength": "20mg",
                "storage_temp_min": 15.0,
                "storage_temp_max": 25.0,
                "storage_humidity_min": 30.0,
                "storage_humidity_max": 60.0,
                "manufacturer": "GastroMed Inc.",
                "ndc": "78901-789-78",
                "status": "active",
                "approval_number": "NDA789012",
            },
            {
                "gtin": "00123456789019",
                "name": "Morphine Sulfate 10mg/mL",
                "description": "Injectable pain medication",
                "form": "injection",
                "strength": "10mg/mL",
                "storage_temp_min": 15.0,
                "storage_temp_max": 25.0,
                "storage_humidity_min": 40.0,
                "storage_humidity_max": 70.0,
                "manufacturer": "PainRelief Pharma",
                "ndc": "89012-890-89",
                "status": "active",
                "approval_number": "NDA890123",
            },
            {
                "gtin": "00123456789020",
                "name": "Bacitracin Ointment",
                "description": "Topical antibiotic ointment",
                "form": "ointment",
                "strength": "500 units/g",
                "storage_temp_min": 15.0,
                "storage_temp_max": 25.0,
                "storage_humidity_min": 25.0,
                "storage_humidity_max": 55.0,
                "manufacturer": "WoundCare Labs",
                "ndc": "90123-901-90",
                "status": "active",
                "approval_number": "NDA901234",
            },
            {
                "gtin": "00123456789021",
                "name": "Azithromycin Powder",
                "description": "Antibiotic powder for reconstitution",
                "form": "powder",
                "strength": "200mg/5mL when reconstituted",
                "storage_temp_min": 15.0,
                "storage_temp_max": 30.0,
                "storage_humidity_min": 20.0,
                "storage_humidity_max": 50.0,
                "manufacturer": "AntiBio Pharma",
                "ndc": "01234-012-01",
                "status": "active",
                "approval_number": "NDA012345",
            },
        ]

        with transaction.atomic():
            for product_data in products_data:
                product, created = m.Product.objects.get_or_create(
                    gtin=product_data["gtin"],
                    defaults=product_data,
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created product: {product.name}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Product already exists: {product.name}")
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {len(products_data)} products")
        )
