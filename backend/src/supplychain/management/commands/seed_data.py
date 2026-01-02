"""
Django management command to seed complete mock data for all models.

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear  # Clear existing data first
"""

import hashlib
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

import supplychain.models as m

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with complete mock data for all models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            self._clear_data()

        with transaction.atomic():
            self.stdout.write("Creating main user...")
            main_user = self._create_main_user()

            self.stdout.write("Creating additional users...")
            users = self._create_additional_users()
            all_users = [main_user] + users

            self.stdout.write("Seeding products...")
            products = self._seed_products()

            self.stdout.write("Seeding batches...")
            batches = self._seed_batches(products)

            self.stdout.write("Seeding packs...")
            packs = self._seed_packs(batches)

            self.stdout.write("Seeding shipments...")
            shipments = self._seed_shipments(packs)

            self.stdout.write("Seeding events...")
            self._seed_events(products, batches, packs, shipments, all_users)

            self.stdout.write("Seeding notification rules...")
            self._seed_notification_rules(all_users)

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Main user (SUPERUSER): teodor (password: teodorpass)"
            )
        )

    def _clear_data(self):
        """Clear all existing data in reverse dependency order."""
        m.NotificationLog.objects.all().delete()
        m.NotificationRule.objects.all().delete()
        m.Document.objects.all().delete()
        m.Event.objects.all().delete()
        m.ShipmentPack.objects.all().delete()
        m.Shipment.objects.all().delete()
        m.Pack.objects.all().delete()
        m.Batch.objects.all().delete()
        m.Product.objects.all().delete()
        m.RoleAssignment.objects.all().delete()
        m.UserProfile.objects.all().delete()
        # Delete all non-superuser users
        User.objects.filter(is_superuser=False).delete()

    def _create_main_user(self):
        """Create or get the main user with all roles."""
        user, created = User.objects.get_or_create(
            email="teodormarinescu84@gmail.com",
            defaults={
                "username": "teodor",
                "first_name": "Main",
                "last_name": "User",
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created or not user.is_superuser:
            user.set_password("teodorpass")
            user.is_superuser = True
            user.is_staff = True
            user.save()

        # Create profile if it doesn't exist
        profile, _ = m.UserProfile.objects.get_or_create(
            user=user,
            defaults={"active_role": "Admin"},
        )

        # Assign all roles
        for role, _ in m.UserProfile.ROLE_CHOICES:
            m.RoleAssignment.objects.get_or_create(user=user, role=role)

        return user

    def _create_additional_users(self):
        """Create additional mock users with various roles."""
        users_data = [
            {
                "username": "operator1",
                "email": "operator1@supplychain.test",
                "first_name": "John",
                "last_name": "Operator",
                "roles": ["Operator"],
                "active_role": "Operator",
            },
            {
                "username": "operator2",
                "email": "operator2@supplychain.test",
                "first_name": "Jane",
                "last_name": "Worker",
                "roles": ["Operator"],
                "active_role": "Operator",
            },
            {
                "username": "auditor1",
                "email": "auditor1@supplychain.test",
                "first_name": "Mike",
                "last_name": "Auditor",
                "roles": ["Auditor"],
                "active_role": "Auditor",
            },
            {
                "username": "admin1",
                "email": "admin1@supplychain.test",
                "first_name": "Sarah",
                "last_name": "Admin",
                "roles": ["Admin", "Operator"],
                "active_role": "Admin",
            },
            {
                "username": "multiuser",
                "email": "multi@supplychain.test",
                "first_name": "Alex",
                "last_name": "MultiRole",
                "roles": ["Operator", "Auditor"],
                "active_role": "Operator",
            },
        ]

        users = []
        for data in users_data:
            roles = data.pop("roles")
            active_role = data.pop("active_role")

            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    **data,
                    "is_active": True,
                },
            )
            if created:
                user.set_password("TestPassword123!")
                user.save()

            profile, _ = m.UserProfile.objects.get_or_create(
                user=user,
                defaults={"active_role": active_role},
            )

            for role in roles:
                m.RoleAssignment.objects.get_or_create(user=user, role=role)

            users.append(user)

        return users

    def _seed_products(self):
        """Seed product data."""
        products_data = [
            {
                "gtin": "00123456789012",
                "name": "Aspirin 325mg",
                "description": "Pain relief and fever reducer tablets",
                "form": "tablet",
                "strength": "325mg",
                "storage_temp_min": Decimal("15.0"),
                "storage_temp_max": Decimal("25.0"),
                "storage_humidity_min": Decimal("30.0"),
                "storage_humidity_max": Decimal("60.0"),
                "manufacturer": "PharmaCorp Inc.",
                "ndc": "12345-123-1",
                "status": "active",
                "approval_number": "NDA123456",
            },
            {
                "gtin": "00123456789013",
                "name": "Amoxicillin 500mg",
                "description": "Antibiotic capsules for bacterial infections",
                "form": "capsule",
                "strength": "500mg",
                "storage_temp_min": Decimal("2.0"),
                "storage_temp_max": Decimal("8.0"),
                "storage_humidity_min": Decimal("40.0"),
                "storage_humidity_max": Decimal("70.0"),
                "manufacturer": "MediLife Labs",
                "ndc": "23456-234-2",
                "status": "active",
                "approval_number": "NDA234567",
            },
            {
                "gtin": "00123456789014",
                "name": "Insulin Glargine 100 units/mL",
                "description": "Long-acting insulin injection for diabetes",
                "form": "injection",
                "strength": "100 units/mL",
                "storage_temp_min": Decimal("2.0"),
                "storage_temp_max": Decimal("8.0"),
                "storage_humidity_min": Decimal("35.0"),
                "storage_humidity_max": Decimal("65.0"),
                "manufacturer": "DiabetesCare Pharma",
                "ndc": "34567-345-3",
                "status": "active",
                "approval_number": "NDA345678",
            },
            {
                "gtin": "00123456789015",
                "name": "Hydrocortisone Cream 1%",
                "description": "Topical anti-inflammatory cream",
                "form": "cream",
                "strength": "1%",
                "storage_temp_min": Decimal("15.0"),
                "storage_temp_max": Decimal("30.0"),
                "storage_humidity_min": Decimal("25.0"),
                "storage_humidity_max": Decimal("55.0"),
                "manufacturer": "SkinCare Solutions",
                "ndc": "45678-456-4",
                "status": "active",
                "approval_number": "NDA456789",
            },
            {
                "gtin": "00123456789016",
                "name": "Acetaminophen Liquid 160mg/5mL",
                "description": "Children's pain and fever reducer",
                "form": "liquid",
                "strength": "160mg/5mL",
                "storage_temp_min": Decimal("20.0"),
                "storage_temp_max": Decimal("25.0"),
                "storage_humidity_min": Decimal("30.0"),
                "storage_humidity_max": Decimal("50.0"),
                "manufacturer": "PediaCare Pharma",
                "ndc": "56789-567-5",
                "status": "active",
                "approval_number": "NDA567890",
            },
            {
                "gtin": "00123456789017",
                "name": "Omeprazole 20mg",
                "description": "Proton pump inhibitor for acid reflux",
                "form": "capsule",
                "strength": "20mg",
                "storage_temp_min": Decimal("15.0"),
                "storage_temp_max": Decimal("25.0"),
                "storage_humidity_min": Decimal("30.0"),
                "storage_humidity_max": Decimal("60.0"),
                "manufacturer": "GastroHealth Labs",
                "ndc": "67890-678-6",
                "status": "active",
                "approval_number": "NDA678901",
            },
            {
                "gtin": "00123456789018",
                "name": "Metformin 500mg",
                "description": "Oral diabetes medication",
                "form": "tablet",
                "strength": "500mg",
                "storage_temp_min": Decimal("15.0"),
                "storage_temp_max": Decimal("30.0"),
                "storage_humidity_min": Decimal("30.0"),
                "storage_humidity_max": Decimal("65.0"),
                "manufacturer": "DiabetesCare Pharma",
                "ndc": "78901-789-7",
                "status": "active",
                "approval_number": "NDA789012",
            },
            {
                "gtin": "00123456789019",
                "name": "Lisinopril 10mg",
                "description": "ACE inhibitor for hypertension",
                "form": "tablet",
                "strength": "10mg",
                "storage_temp_min": Decimal("20.0"),
                "storage_temp_max": Decimal("25.0"),
                "storage_humidity_min": Decimal("35.0"),
                "storage_humidity_max": Decimal("55.0"),
                "manufacturer": "CardioHealth Inc.",
                "ndc": "89012-890-8",
                "status": "active",
                "approval_number": "NDA890123",
            },
            {
                "gtin": "00123456789020",
                "name": "Salbutamol Inhaler 100mcg",
                "description": "Bronchodilator inhaler for asthma",
                "form": "inhaler",
                "strength": "100mcg",
                "storage_temp_min": Decimal("15.0"),
                "storage_temp_max": Decimal("25.0"),
                "storage_humidity_min": Decimal("30.0"),
                "storage_humidity_max": Decimal("50.0"),
                "manufacturer": "RespiCare Pharma",
                "ndc": "90123-901-9",
                "status": "active",
                "approval_number": "NDA901234",
            },
            {
                "gtin": "00123456789021",
                "name": "Atorvastatin 40mg (Discontinued)",
                "description": "Cholesterol-lowering medication",
                "form": "tablet",
                "strength": "40mg",
                "storage_temp_min": Decimal("15.0"),
                "storage_temp_max": Decimal("25.0"),
                "storage_humidity_min": Decimal("30.0"),
                "storage_humidity_max": Decimal("60.0"),
                "manufacturer": "CardioHealth Inc.",
                "ndc": "01234-012-0",
                "status": "discontinued",
                "approval_number": "NDA012345",
            },
        ]

        products = []
        for data in products_data:
            product, _ = m.Product.objects.get_or_create(
                gtin=data["gtin"],
                defaults=data,
            )
            products.append(product)

        return products

    def _seed_batches(self, products):
        """Seed batch data for products."""
        batches = []
        now = timezone.now().date()

        batch_configs = [
            # (days_ago_manufactured, months_until_expiry, qty, status, location, facility)
            (7, 24, 12000, "active", "New York, NY", "NYC Manufacturing Plant"),
            (14, 24, 11000, "active", "Los Angeles, CA", "LA Pharma Facility"),
            (21, 22, 10000, "active", "Chicago, IL", "Chicago Distribution Center"),
            (30, 20, 9500, "active", "Houston, TX", "Texas Pharma Hub"),
            (45, 18, 8000, "released", "Miami, FL", "Florida Medical Center"),
            (60, 18, 7500, "active", "Phoenix, AZ", "Arizona Pharma Complex"),
            (75, 15, 7000, "released", "Boston, MA", "Boston Labs"),
            (90, 12, 6500, "active", "Denver, CO", "Rocky Mountain Facility"),
            (120, 10, 6000, "active", "Seattle, WA", "Pacific Northwest Plant"),
            (150, 8, 5000, "released", "Atlanta, GA", "Southeast Distribution Hub"),
            (180, 6, 4000, "released", "Dallas, TX", "Texas Regional Center"),
            (210, 4, 3500, "active", "Philadelphia, PA", "Northeast Pharma Facility"),
            (240, 3, 3000, "active", "San Diego, CA", "West Coast Labs"),
            (270, 2, 2500, "active", "Detroit, MI", "Great Lakes Manufacturing"),
            (300, 1, 2000, "active", "Minneapolis, MN", "Midwest Pharma Center"),
            (330, 0.5, 1500, "active", "Portland, OR", "Pacific Northwest Hub"),
            (365, -1, 1000, "expired", "Columbus, OH", "Central Ohio Plant"),
            (395, -2, 800, "expired", "Indianapolis, IN", "Midwest Medical Supply"),
            (20, 15, 5000, "quarantined", "Nashville, TN", "Tennessee Pharma Lab"),
            (50, 12, 4500, "quarantined", "Charlotte, NC", "Carolina Medical Center"),
        ]

        for i, product in enumerate(products):
            # Each product gets 4-6 batches for better analytics
            num_batches = random.randint(4, 6)
            for j in range(num_batches):
                config = batch_configs[(i + j) % len(batch_configs)]
                days_ago, months_exp, qty, status, location, facility = config

                mfg_date = now - timedelta(days=days_ago)
                exp_date = now + timedelta(days=months_exp * 30)

                lot_number = f"LOT-{product.gtin[-4:]}-{mfg_date.strftime('%Y%m')}-{j + 1:03d}"

                batch, _ = m.Batch.objects.get_or_create(
                    product=product,
                    lot_number=lot_number,
                    defaults={
                        "manufacturing_date": mfg_date,
                        "expiry_date": exp_date,
                        "quantity_produced": qty,
                        "available_quantity": int(qty * random.uniform(0.3, 0.9)),
                        "manufacturing_location": location,
                        "manufacturing_facility": facility,
                        "status": status,
                        "quality_control_passed": status != "quarantined",
                        "quality_control_notes": f"QC check completed on {mfg_date + timedelta(days=1)}",
                        "batch_size": f"{qty} units",
                        "supplier_batch_number": f"SUP-{random.randint(10000, 99999)}",
                        "regulatory_approval_number": f"REG-{random.randint(1000, 9999)}",
                        "certificate_of_analysis": f"COA-{lot_number}",
                    },
                )
                batches.append(batch)

        return batches

    def _seed_packs(self, batches):
        """Seed pack data for batches."""
        packs = []
        pack_types = ["bottle", "box", "blister", "vial", "tube", "sachet"]
        # Most packs should be active (available for shipping)
        statuses = ["active", "active", "active", "active", "shipped", "delivered"]
        locations = [
            "Warehouse A - Section 1",
            "Warehouse A - Section 2",
            "Warehouse B - Cold Storage",
            "Distribution Center 1",
            "Distribution Center 2",
            "Retail Partner - CVS",
            "Retail Partner - Walgreens",
        ]

        pack_counter = 1
        for batch in batches:
            # Each batch gets 10-25 packs for better analytics
            num_packs = random.randint(10, 25)
            for _ in range(num_packs):
                serial_number = f"SN-{batch.lot_number[-7:]}-{pack_counter:06d}"
                pack_type = random.choice(pack_types)
                status = random.choice(statuses)
                location = random.choice(locations)

                pack, _ = m.Pack.objects.get_or_create(
                    serial_number=serial_number,
                    defaults={
                        "batch": batch,
                        "pack_size": random.choice([10, 20, 30, 50, 100]),
                        "pack_type": pack_type,
                        "status": status,
                        "location": location,
                        "warehouse_section": location.split(" - ")[-1] if " - " in location else "Main",
                        "quality_control_passed": True,
                        "quality_control_notes": "Pack verified during production",
                        "regulatory_code": f"RC-{random.randint(10000, 99999)}",
                        # Don't set shipped_date or delivered_date here - let shipments handle that
                    },
                )
                packs.append(pack)
                pack_counter += 1

        return packs

    def _seed_shipments(self, packs):
        """Seed shipment data."""
        shipments = []
        now = timezone.now()

        carriers = ["fedex", "ups", "dhl", "usps", "local", "internal"]
        service_types = ["standard", "express", "overnight", "ground", "cold_chain"]
        temp_requirements = ["ambient", "cool", "frozen", "ultra_cold", "controlled"]
        
        # Define carrier-specific damage rates (some carriers are more reliable)
        # These are higher than real-world rates for demonstration purposes
        carrier_damage_rates = {
            "fedex": 0.03,   # 3% damage rate
            "ups": 0.015,    # 1.5% damage rate (most reliable)
            "dhl": 0.04,     # 4% damage rate
            "usps": 0.05,    # 5% damage rate
            "local": 0.06,   # 6% damage rate
            "internal": 0.025, # 2.5% damage rate
        }
        
        statuses = [
            "pending",
            "confirmed",
            "picked_up",
            "in_transit",
            "delivered",
            "delivered",
            "delivered",
            "delivered",
        ]

        origins = [
            ("PharmaCorp Warehouse", "123 Industrial Blvd", "New York", "NY", "10001", "USA"),
            ("MediLife Distribution", "456 Pharma Way", "Los Angeles", "CA", "90001", "USA"),
            ("DiabetesCare Hub", "789 Health Center Dr", "Chicago", "IL", "60601", "USA"),
            ("HealthFirst Supply", "321 Medical Plaza", "Phoenix", "AZ", "85001", "USA"),
            ("BioPharma Logistics", "555 Science Park Dr", "San Diego", "CA", "92101", "USA"),
        ]

        destinations = [
            ("City Hospital Pharmacy", "100 Medical Center Dr", "Boston", "MA", "02101", "USA"),
            ("CVS Pharmacy #1234", "200 Main Street", "Miami", "FL", "33101", "USA"),
            ("Walgreens #5678", "300 Oak Avenue", "Dallas", "TX", "75201", "USA"),
            ("Regional Medical Center", "400 Hospital Ln", "Seattle", "WA", "98101", "USA"),
            ("Community Health Clinic", "500 Wellness Blvd", "Denver", "CO", "80201", "USA"),
            ("University Hospital", "600 Campus Dr", "Ann Arbor", "MI", "48109", "USA"),
            ("Memorial Hospital", "700 Healthcare Way", "Atlanta", "GA", "30303", "USA"),
            ("Central Pharmacy", "800 Downtown Ave", "Portland", "OR", "97201", "USA"),
        ]

        # Create 120 shipments distributed across 90 days for better daily volume analytics
        shipped_packs = [p for p in packs if p.status in ["shipped", "delivered"]]
        available_packs = [p for p in packs if p.status == "active"]
        
        # Create varied daily volumes - some days have many shipments, some have few
        shipments_by_day = {}
        for day_offset in range(90):
            # Vary volume: weekdays have more, weekends have less, some peaks and valleys
            base_volume = random.randint(0, 4)
            day_of_week = (now - timedelta(days=day_offset)).weekday()
            if day_of_week >= 5:  # Weekend
                volume = max(0, base_volume - 1)
            else:  # Weekday
                volume = base_volume
            
            # Add some peak days (10% of days have extra volume)
            if random.random() < 0.1:
                volume += random.randint(2, 5)
            
            shipments_by_day[day_offset] = volume

        shipment_count = 0
        damaged_count = 0
        lost_count = 0
        for day_offset in range(90):
            num_shipments = shipments_by_day[day_offset]
            
            for j in range(num_shipments):
                shipment_count += 1
                tracking_number = f"SHIP-2025-{shipment_count:06d}"
                carrier = random.choice(carriers)
                service = random.choice(service_types)
                origin = random.choice(origins)
                destination = random.choice(destinations)
                temp_req = random.choice(temp_requirements)
                
                # Determine status - first pick from base statuses, then apply carrier-specific damage/loss rates
                base_status = random.choice(statuses)
                
                # Apply carrier-specific damage rate only to shipments that would otherwise be delivered
                if base_status == "delivered":
                    damage_rate = carrier_damage_rates.get(carrier, 0.015)
                    loss_rate = damage_rate * 0.2  # Loss rate is typically 20% of damage rate
                    
                    rand = random.random()
                    if rand < loss_rate:
                        status = "lost"
                        lost_count += 1
                    elif rand < (loss_rate + damage_rate):
                        status = "damaged"
                        damaged_count += 1
                    else:
                        status = "delivered"
                else:
                    status = base_status

                # Calculate dates based on day_offset and status
                if status in ["pending", "confirmed"]:
                    shipped_date = None
                    est_delivery = now + timedelta(days=random.randint(1, 7))
                    actual_delivery = None
                elif status == "delivered":
                    shipped_date = now - timedelta(days=day_offset)
                    days_to_deliver = random.randint(1, 5)
                    actual_delivery = shipped_date + timedelta(days=days_to_deliver)
                    est_delivery = shipped_date + timedelta(days=days_to_deliver + random.randint(-1, 2))
                elif status in ["damaged", "lost"]:
                    # Damaged/lost shipments were shipped but had issues
                    shipped_date = now - timedelta(days=day_offset)
                    est_delivery = shipped_date + timedelta(days=random.randint(2, 7))
                    # Actual delivery date is when issue was identified
                    actual_delivery = shipped_date + timedelta(days=random.randint(1, 5))
                else:  # picked_up or in_transit
                    shipped_date = now - timedelta(days=day_offset)
                    est_delivery = now + timedelta(days=random.randint(1, 5))
                    actual_delivery = None

                shipment, created = m.Shipment.objects.get_or_create(
                    tracking_number=tracking_number,
                    defaults={
                        "status": status,
                        "carrier": carrier,
                        "service_type": service,
                        "origin_name": origin[0],
                        "origin_address_line1": origin[1],
                        "origin_city": origin[2],
                        "origin_state": origin[3],
                        "origin_postal_code": origin[4],
                        "origin_country": origin[5],
                        "destination_name": destination[0],
                        "destination_address_line1": destination[1],
                        "destination_city": destination[2],
                        "destination_state": destination[3],
                        "destination_postal_code": destination[4],
                        "destination_country": destination[5],
                        "shipped_date": shipped_date,
                        "estimated_delivery_date": est_delivery,
                        "actual_delivery_date": actual_delivery,
                        "temperature_requirement": temp_req,
                        "special_handling_required": temp_req in ["frozen", "ultra_cold"],
                        "special_instructions": "Handle with care" if temp_req != "ambient" else "",
                        "shipping_cost": Decimal(str(random.uniform(50, 500))).quantize(Decimal("0.01")),
                        "currency": "USD",
                        "notes": f"Shipment {shipment_count} - {service} delivery",
                    },
                )

                if created:
                    # Add 1-4 packs to each shipment
                    num_packs = min(random.randint(1, 4), len(available_packs))
                    packs_to_add = available_packs[:num_packs]
                    for pack in packs_to_add:
                        m.ShipmentPack.objects.get_or_create(
                            shipment=shipment,
                            pack=pack,
                            defaults={
                                "quantity_shipped": 1,
                                "notes": f"Added to shipment {tracking_number}",
                            },
                        )
                        if len(available_packs) > 5:
                            available_packs.remove(pack)
                
                shipments.append(shipment)

        self.stdout.write(f"  Created {shipment_count} shipments ({damaged_count} damaged, {lost_count} lost)")
        return shipments

    def _seed_events(self, products, batches, packs, shipments, users):
        """Seed event data for audit trail."""
        event_types = [
            "created",
            "updated",
            "status_changed",
            "quality_check",
            "shipped",
            "delivered",
            "temperature_alert",
            "temperature_excursion",
            "packed",
            "unpacked",
            "recalled",
        ]
        severities = ["info", "low", "medium", "high", "critical"]
        now = timezone.now()

        events_created = 0
        
        def create_event_with_date(days_ago, **kwargs):
            """Helper to create event with custom created_at date (bypassing auto_now_add)."""
            event = m.Event.objects.create(**kwargs)
            # Update created_at manually to bypass auto_now_add
            m.Event.objects.filter(id=event.id).update(created_at=now - timedelta(days=days_ago))
            return event

        # Events for products - all products with varied event history
        for product in products:
            content_type = ContentType.objects.get_for_model(product)
            for j in range(random.randint(3, 8)):
                event_type = random.choice(["created", "updated", "status_changed"])
                days_ago = random.randint(1, 365)
                create_event_with_date(
                    days_ago=days_ago,
                    event_type=event_type,
                    entity_type="product",
                    entity_id=product.id,
                    content_type=content_type,
                    description=f"Product {product.name}: {event_type} event",
                    metadata={"gtin": product.gtin, "action": event_type},
                    severity=random.choice(severities),
                    location=product.manufacturer,
                    user=random.choice(users),
                )
                events_created += 1

        # Events for batches - all batches with comprehensive history including temperature events
        for batch in batches:
            content_type = ContentType.objects.get_for_model(batch)
            
            # Regular events
            for j in range(random.randint(3, 8)):
                event_type = random.choice(event_types[:6])
                days_ago = random.randint(1, 365)
                create_event_with_date(
                    days_ago=days_ago,
                    event_type=event_type,
                    entity_type="batch",
                    entity_id=batch.id,
                    content_type=content_type,
                    description=f"Batch {batch.lot_number}: {event_type} event",
                    metadata={"lot_number": batch.lot_number, "status": batch.status},
                    severity=random.choice(severities),
                    location=batch.manufacturing_location,
                    user=random.choice(users),
                )
                events_created += 1
            
            # Add temperature excursion events for some batches (30% chance)
            # Spread these across 100-180 days ago (no overlap with shipments at 0-90 days)
            if random.random() < 0.3:
                for k in range(random.randint(1, 3)):
                    days_ago = random.randint(100, 180)
                    temp_recorded = random.uniform(-5, 35)
                    temp_min = float(batch.product.storage_temp_min or 2)
                    temp_max = float(batch.product.storage_temp_max or 8)
                    
                    create_event_with_date(
                        days_ago=days_ago,
                        event_type="temperature_excursion",
                        entity_type="batch",
                        entity_id=batch.id,
                        content_type=content_type,
                        description=f"Temperature excursion detected for batch {batch.lot_number}: {temp_recorded:.1f}°C (acceptable range: {temp_min}-{temp_max}°C)",
                        metadata={
                            "lot_number": batch.lot_number,
                            "temperature_recorded": round(temp_recorded, 1),
                            "temperature_min": temp_min,
                            "temperature_max": temp_max,
                            "duration_minutes": random.randint(5, 120),
                        },
                        severity="high" if abs(temp_recorded - (temp_min + temp_max) / 2) > 5 else "medium",
                        location=batch.manufacturing_location,
                        user=random.choice(users),
                    )
                    events_created += 1

        # Events for packs - more packs for better analytics with temperature monitoring
        for pack in packs[:200]:
            content_type = ContentType.objects.get_for_model(pack)
            for j in range(random.randint(2, 5)):
                event_type = random.choice(event_types[:8])
                days_ago = random.randint(1, 180)
                create_event_with_date(
                    days_ago=days_ago,
                    event_type=event_type,
                    entity_type="pack",
                    entity_id=pack.id,
                    content_type=content_type,
                    description=f"Pack {pack.serial_number}: {event_type} event",
                    metadata={"serial_number": pack.serial_number, "status": pack.status},
                    severity=random.choice(severities),
                    location=pack.location,
                    user=random.choice(users),
                )
                events_created += 1
            
            # Add temperature alerts for some packs in transit (20% chance)
            # Spread these across 100-150 days ago (completely separate from shipments)
            if pack.status in ["shipped", "delivered"] and random.random() < 0.2:
                days_ago = random.randint(100, 150)
                temp_recorded = random.uniform(-2, 30)
                temp_min = float(pack.batch.product.storage_temp_min or 2)
                temp_max = float(pack.batch.product.storage_temp_max or 8)
                
                create_event_with_date(
                    days_ago=days_ago,
                    event_type="temperature_alert",
                    entity_type="pack",
                    entity_id=pack.id,
                    content_type=content_type,
                    description=f"Temperature alert for pack {pack.serial_number} during transit: {temp_recorded:.1f}°C",
                    metadata={
                        "serial_number": pack.serial_number,
                        "temperature_recorded": round(temp_recorded, 1),
                        "temperature_min": temp_min,
                        "temperature_max": temp_max,
                    },
                    severity="medium",
                    location=pack.location,
                    user=random.choice(users),
                )
                events_created += 1

        # Events for shipments - all shipments with detailed history
        for shipment in shipments:
            content_type = ContentType.objects.get_for_model(shipment)
            for j in range(random.randint(3, 7)):
                event_type = random.choice(["created", "status_changed", "shipped", "delivered", "updated"])
                days_ago = random.randint(1, 90)
                create_event_with_date(
                    days_ago=days_ago,
                    event_type=event_type,
                    entity_type="shipment",
                    entity_id=shipment.id,
                    content_type=content_type,
                    description=f"Shipment {shipment.tracking_number}: {event_type} event",
                    metadata={
                        "tracking_number": shipment.tracking_number,
                        "status": shipment.status,
                        "carrier": shipment.carrier,
                    },
                    severity=random.choice(severities),
                    location=f"{shipment.origin_city} to {shipment.destination_city}",
                    user=random.choice(users),
                )
                events_created += 1
            
            # Add temperature excursion events for shipments with temperature requirements (25% chance)
            # Only create for non-ambient shipments that are shipped or delivered
            if (shipment.temperature_requirement != "ambient" and 
                shipment.status in ["shipped", "in_transit", "delivered", "damaged"] and
                random.random() < 0.25):
                days_ago = random.randint(1, 90)
                
                # Define temperature ranges based on requirement
                temp_ranges = {
                    "cool": (2, 8),
                    "frozen": (-25, -15),
                    "ultra_cold": (-80, -70),
                    "controlled": (15, 25),
                }
                temp_min, temp_max = temp_ranges.get(shipment.temperature_requirement, (2, 8))
                
                # Generate an out-of-range temperature
                if random.random() < 0.5:
                    # Temperature too high
                    temp_recorded = temp_max + random.uniform(2, 10)
                else:
                    # Temperature too low
                    temp_recorded = temp_min - random.uniform(2, 10)
                
                create_event_with_date(
                    days_ago=days_ago,
                    event_type="temperature_excursion",
                    entity_type="shipment",
                    entity_id=shipment.id,
                    content_type=content_type,
                    description=f"Temperature excursion detected for shipment {shipment.tracking_number}: {temp_recorded:.1f}°C (required range: {temp_min} to {temp_max}°C)",
                    metadata={
                        "tracking_number": shipment.tracking_number,
                        "temperature_recorded": round(temp_recorded, 1),
                        "temperature_min": temp_min,
                        "temperature_max": temp_max,
                        "temperature_requirement": shipment.temperature_requirement,
                        "duration_minutes": random.randint(10, 180),
                    },
                    severity="critical" if abs(temp_recorded - (temp_min + temp_max) / 2) > 8 else "high",
                    location=f"In transit: {shipment.origin_city} to {shipment.destination_city}",
                    user=random.choice(users),
                )
                events_created += 1
            
            # Add specific damage/lost events for damaged or lost shipments
            if shipment.status == "damaged":
                days_ago = random.randint(1, 90)
                damage_reasons = [
                    "Package crushed during transit",
                    "Water damage detected",
                    "Temperature excursion caused product degradation",
                    "Rough handling by carrier",
                    "Packaging integrity compromised",
                ]
                create_event_with_date(
                    days_ago=days_ago,
                    event_type="damaged",
                    entity_type="shipment",
                    entity_id=shipment.id,
                    content_type=content_type,
                    description=f"Shipment {shipment.tracking_number} damaged: {random.choice(damage_reasons)}",
                    metadata={
                        "tracking_number": shipment.tracking_number,
                        "carrier": shipment.carrier,
                        "damage_type": random.choice(["physical", "environmental", "handling"]),
                        "reported_by": random.choice(["carrier", "recipient", "inspector"]),
                    },
                    severity="high",
                    location=f"{shipment.destination_city}",
                    user=random.choice(users),
                )
                events_created += 1
            
            elif shipment.status == "lost":
                days_ago = random.randint(1, 90)
                create_event_with_date(
                    days_ago=days_ago,
                    event_type="alert",
                    entity_type="shipment",
                    entity_id=shipment.id,
                    content_type=content_type,
                    description=f"Shipment {shipment.tracking_number} reported lost by {shipment.carrier}",
                    metadata={
                        "tracking_number": shipment.tracking_number,
                        "carrier": shipment.carrier,
                        "last_known_location": random.choice([shipment.origin_city, shipment.destination_city]),
                    },
                    severity="critical",
                    location=f"Unknown - Last seen: {shipment.origin_city}",
                    user=random.choice(users),
                )
                events_created += 1

        self.stdout.write(f"  Created {events_created} events")

    def _seed_notification_rules(self, users):
        """Seed notification rules for users."""
        rule_configs = [
            {
                "name": "Critical Alerts",
                "event_types": ["recalled", "damaged", "expired", "error"],
                "severity_levels": ["high", "critical"],
                "channels": ["email", "websocket"],
            },
            {
                "name": "Shipment Updates",
                "event_types": ["shipped", "delivered", "returned"],
                "severity_levels": [],
                "channels": ["websocket"],
            },
            {
                "name": "Quality Control",
                "event_types": ["quality_check", "temperature_alert"],
                "severity_levels": ["medium", "high", "critical"],
                "channels": ["email"],
            },
            {
                "name": "All Events",
                "event_types": [],
                "severity_levels": [],
                "channels": ["websocket"],
            },
        ]

        for user in users:
            # Give each user 1-2 notification rules
            num_rules = random.randint(1, 2)
            selected_configs = random.sample(rule_configs, num_rules)

            for config in selected_configs:
                m.NotificationRule.objects.get_or_create(
                    user=user,
                    name=config["name"],
                    defaults={
                        "event_types": config["event_types"],
                        "severity_levels": config["severity_levels"],
                        "channels": config["channels"],
                        "enabled": True,
                    },
                )
