#!/usr/bin/env python
"""
Test script for the notification system.

This script demonstrates how to:
1. Create notification rules
2. Trigger events that send notifications
3. Check notification logs
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
django.setup()

from django.contrib.auth import get_user_model
from supplychain.models import (
    NotificationRule,
    NotificationLog,
    Event,
    Product,
    Batch,
)

User = get_user_model()


def create_test_user():
    """Create or get a test user."""
    user, created = User.objects.get_or_create(
        username="test_admin",
        defaults={
            "email": "admin@example.com",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if created:
        user.set_password("admin123")
        user.save()
        print(f"✅ Created test user: {user.username} ({user.email})")
    else:
        print(f"ℹ️  Using existing user: {user.username} ({user.email})")
    return user


def create_notification_rule(user):
    """Create a notification rule for critical events."""
    rule, created = NotificationRule.objects.get_or_create(
        user=user,
        name="Critical Alerts - Email",
        defaults={
            "event_types": ["recalled", "temperature_alert", "damaged"],
            "severity_levels": ["critical", "high"],
            "channels": ["email"],
            "enabled": True,
        },
    )
    if created:
        print(f"✅ Created notification rule: {rule.name}")
    else:
        print(f"ℹ️  Using existing notification rule: {rule.name}")
    return rule


def create_test_product():
    """Create a test product."""
    product, created = Product.objects.get_or_create(
        gtin="00012345678905",
        defaults={
            "name": "Test Vaccine",
            "form": "Injection",
            "manufacturer": "Test Pharma",
            "status": "active",
        },
    )
    if created:
        print(f"✅ Created test product: {product.name}")
    else:
        print(f"ℹ️  Using existing product: {product.name}")
    return product


def create_test_batch(product):
    """Create a test batch."""
    from datetime import datetime, timedelta

    batch, created = Batch.objects.get_or_create(
        lot_number="LOT-TEST-2026-001",
        product=product,
        defaults={
            "manufacturing_date": datetime.now().date(),
            "expiry_date": (datetime.now() + timedelta(days=365)).date(),
            "quantity_produced": 1000,
            "available_quantity": 1000,
            "status": "active",
        },
    )
    if created:
        print(f"✅ Created test batch: {batch.lot_number}")
    else:
        print(f"ℹ️  Using existing batch: {batch.lot_number}")
    return batch


def trigger_critical_event(batch, user):
    """Trigger a critical event that should send a notification."""
    print("\n" + "=" * 60)
    print("TRIGGERING CRITICAL EVENT")
    print("=" * 60)

    event = Event.create_event(
        event_type="recalled",
        entity_type="batch",
        entity_id=batch.id,
        description=f"CRITICAL: Batch {batch.lot_number} has been recalled due to quality issues",
        user=user,
        severity="critical",
        metadata={
            "reason": "Failed quality control",
            "action_required": "Immediate retrieval from distribution",
            "affected_units": 1000,
        },
    )

    print(f"✅ Created event: {event.event_type} (severity: {event.severity})")
    print(f"   Description: {event.description}")
    print(f"   Event ID: {event.id}")

    # The notification task should be queued automatically via signals
    print("\n🔔 Notification task queued to RabbitMQ!")
    print("   Check Celery worker logs to see task processing...")

    return event


def check_notification_logs(event):
    """Check notification logs for the event."""
    print("\n" + "=" * 60)
    print("NOTIFICATION LOGS")
    print("=" * 60)

    notifications = NotificationLog.objects.filter(event=event)

    if notifications.exists():
        for notif in notifications:
            status_icon = {
                "pending": "⏳",
                "sent": "✅",
                "failed": "❌",
                "acknowledged": "✔️",
            }.get(notif.status, "❓")

            print(f"\n{status_icon} Notification #{notif.id}")
            print(f"   To: {notif.user.username} ({notif.user.email})")
            print(f"   Channel: {notif.channel}")
            print(f"   Status: {notif.status}")
            if notif.sent_at:
                print(f"   Sent at: {notif.sent_at}")
            if notif.error_message:
                print(f"   Error: {notif.error_message}")
    else:
        print("⚠️  No notifications found yet.")
        print("   Note: Notifications are processed asynchronously.")
        print("   Check again in a few seconds or look at Celery worker logs.")


def main():
    print("\n" + "=" * 60)
    print("NOTIFICATION SYSTEM TEST")
    print("=" * 60 + "\n")

    # Setup
    user = create_test_user()
    rule = create_notification_rule(user)
    product = create_test_product()
    batch = create_test_batch(product)

    # Trigger event
    event = trigger_critical_event(batch, user)

    # Check logs (might be empty if task hasn't processed yet)
    import time

    time.sleep(2)  # Wait for async task
    check_notification_logs(event)

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("   1. Check Celery worker logs for task execution")
    print("   2. Check RabbitMQ management UI: http://localhost:15672")
    print("   3. Configure SMTP settings to send real emails")
    print("   4. View notification rules in Django Admin: http://localhost:8000/admin")
    print()


if __name__ == "__main__":
    main()
