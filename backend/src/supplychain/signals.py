"""
Django signals for automated event generation in the supply chain system.

This module sets up post_save, post_delete, and custom signals to automatically
create events when supply chain entities are modified. This provides a complete
audit trail without requiring manual event creation.
"""

import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

import supplychain.models as m

from .middleware import get_current_user

User = get_user_model()
logger = logging.getLogger(__name__)


def get_field_changes(instance, created=False):
    """
    Get the fields that changed in a model instance.
    Returns a dictionary of field changes for event metadata.
    """
    if created:
        # For new instances, all fields are considered "changed"
        changes = {}
        for field in instance._meta.fields:
            value = getattr(instance, field.name, None)
            if value is not None:
                # Convert to string representation for JSON serialization
                if hasattr(value, "isoformat"):  # datetime/date fields
                    changes[field.name] = {"new": value.isoformat()}
                else:
                    changes[field.name] = {"new": str(value)}
        return changes

    # For existing instances, try to use model_utils tracker if available
    changes = {}

    # Check if the model has a FieldTracker (from django-model-utils)
    if hasattr(instance, "_field_tracker"):
        tracker = instance._field_tracker
        for field_name in tracker.fields:
            if tracker.has_changed(field_name):
                old_value = tracker.previous(field_name)
                new_value = getattr(instance, field_name, None)

                # Convert values to string representation for JSON serialization
                if hasattr(old_value, "isoformat"):
                    old_value = old_value.isoformat()
                elif old_value is not None:
                    old_value = str(old_value)

                if hasattr(new_value, "isoformat"):
                    new_value = new_value.isoformat()
                elif new_value is not None:
                    new_value = str(new_value)

                changes[field_name] = {"old": old_value, "new": new_value}

    # If no tracker or no changes detected, return a generic update indicator
    if not changes:
        changes = {"updated": "Changes detected but not tracked"}

    return changes


def create_automated_event(
    event_type, instance, description, severity="info", metadata=None, user=None
):
    """
    Create an automated event for a model instance.

    Args:
        event_type: Type of event (created, updated, deleted, etc.)
        instance: The model instance that triggered the event
        description: Human-readable description of what happened
        severity: Event severity level
        metadata: Additional event data
        user: User who triggered the action (if available)
    """
    # Determine entity type based on model
    entity_type_map = {
        m.Product: "product",
        m.Batch: "batch",
        m.Pack: "pack",
        m.Shipment: "shipment",
    }

    entity_type = entity_type_map.get(type(instance))
    if not entity_type:
        return  # Skip if not a tracked entity type

    # Get user from request context
    if user is None:
        user = get_current_user()
    
    # Ensure user is a valid User instance or None (not AnonymousUser)
    if user and not user.is_authenticated:
        user = None

    # Combine default metadata with provided metadata
    default_metadata = {
        "automated": True,
        "trigger": "django_signal",
        "model": instance.__class__.__name__,
    }

    if metadata:
        default_metadata.update(metadata)

    # Create the event
    # Note: The event_post_save signal will automatically queue notifications
    # for this event, so we don't need to do it here
    try:
        event = m.Event.create_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=instance.id,
            description=description,
            user=user,
            severity=severity,
            metadata=default_metadata,
        )

    except Exception as e:
        # Log the error but don't fail the original operation
        logger.error(
            f"Failed to create automated event for {instance.__class__.__name__} "
            f"(id={instance.id}): {e}",
            exc_info=True
        )


# Product signals
@receiver(post_save, sender=m.Product)
def product_post_save(sender, instance, created, **kwargs):
    """Handle Product creation and updates."""
    if created:
        create_automated_event(
            event_type="created",
            instance=instance,
            description=f"Product '{instance.name}' (GTIN: {instance.gtin}) was created",
            metadata={
                "product_name": instance.name,
                "gtin": instance.gtin,
                "form": instance.form,
                "status": instance.status,
            },
        )
    else:
        # Get field changes (simplified for now)
        changes = get_field_changes(instance, created=False)
        create_automated_event(
            event_type="updated",
            instance=instance,
            description=f"Product '{instance.name}' (GTIN: {instance.gtin}) was updated",
            metadata={
                "product_name": instance.name,
                "gtin": instance.gtin,
                "changes": changes,
            },
        )


@receiver(post_delete, sender=m.Product)
def product_post_delete(sender, instance, **kwargs):
    """Handle Product deletion."""
    create_automated_event(
        event_type="deleted",
        instance=instance,
        description=f"Product '{instance.name}' (GTIN: {instance.gtin}) was deleted",
        severity="medium",
        metadata={
            "product_name": instance.name,
            "gtin": instance.gtin,
            "deleted_fields": {
                "name": instance.name,
                "gtin": instance.gtin,
                "form": instance.form,
                "status": instance.status,
            },
        },
    )


# Batch signals
@receiver(post_save, sender=m.Batch)
def batch_post_save(sender, instance, created, **kwargs):
    """Handle Batch creation and updates."""
    if created:
        create_automated_event(
            event_type="created",
            instance=instance,
            description=f"Batch '{instance.lot_number}' for product '{instance.product.name}' was created",
            metadata={
                "lot_number": instance.lot_number,
                "product_name": instance.product.name,
                "product_gtin": instance.product.gtin,
                "manufacturing_date": instance.manufacturing_date.isoformat(),
                "expiry_date": instance.expiry_date.isoformat(),
                "quantity_produced": instance.quantity_produced,
                "status": instance.status,
            },
        )
    else:
        changes = get_field_changes(instance, created=False)

        # Check if status changed specifically
        if "status" in changes and changes["status"].get("old") != changes[
            "status"
        ].get("new"):
            old_status = changes["status"]["old"]
            new_status = changes["status"]["new"]

            # Create specific status change event
            create_status_change_event(instance, old_status, new_status)

        # Check if batch has expired and create critical event
        from django.utils import timezone
        if instance.expiry_date and instance.expiry_date < timezone.now().date():
            if instance.status not in ["expired", "destroyed"]:
                create_automated_event(
                    event_type="expired",
                    instance=instance,
                    description=f"Batch '{instance.lot_number}' has expired (expiry: {instance.expiry_date})",
                    severity="critical",
                    metadata={
                        "lot_number": instance.lot_number,
                        "product_name": instance.product.name,
                        "expiry_date": instance.expiry_date.isoformat(),
                        "current_status": instance.status,
                    },
                )

        create_automated_event(
            event_type="updated",
            instance=instance,
            description=f"Batch '{instance.lot_number}' for product '{instance.product.name}' was updated",
            metadata={
                "lot_number": instance.lot_number,
                "product_name": instance.product.name,
                "changes": changes,
            },
        )


@receiver(post_delete, sender=m.Batch)
def batch_post_delete(sender, instance, **kwargs):
    """Handle Batch deletion."""
    create_automated_event(
        event_type="deleted",
        instance=instance,
        description=f"Batch '{instance.lot_number}' for product '{instance.product.name}' was deleted",
        severity="medium",
        metadata={
            "lot_number": instance.lot_number,
            "product_name": instance.product.name,
            "product_gtin": instance.product.gtin,
            "deleted_fields": {
                "lot_number": instance.lot_number,
                "manufacturing_date": instance.manufacturing_date.isoformat(),
                "expiry_date": instance.expiry_date.isoformat(),
                "quantity_produced": instance.quantity_produced,
                "status": instance.status,
            },
        },
    )


# Pack signals
@receiver(post_save, sender=m.Pack)
def pack_post_save(sender, instance, created, **kwargs):
    """Handle Pack creation and updates."""
    if created:
        create_automated_event(
            event_type="created",
            instance=instance,
            description=f"Pack '{instance.serial_number}' from batch '{instance.batch.lot_number}' was created",
            metadata={
                "serial_number": instance.serial_number,
                "batch_lot_number": instance.batch.lot_number,
                "product_name": instance.batch.product.name,
                "pack_size": instance.pack_size,
                "pack_type": instance.pack_type,
                "status": instance.status,
                "location": instance.location,
            },
        )
    else:
        changes = get_field_changes(instance, created=False)

        # Check if status changed specifically
        if "status" in changes and changes["status"].get("old") != changes[
            "status"
        ].get("new"):
            old_status = changes["status"]["old"]
            new_status = changes["status"]["new"]

            # Create specific status change event
            create_status_change_event(instance, old_status, new_status)

        create_automated_event(
            event_type="updated",
            instance=instance,
            description=f"Pack '{instance.serial_number}' from batch '{instance.batch.lot_number}' was updated",
            metadata={
                "serial_number": instance.serial_number,
                "batch_lot_number": instance.batch.lot_number,
                "product_name": instance.batch.product.name,
                "changes": changes,
            },
        )


@receiver(post_delete, sender=m.Pack)
def pack_post_delete(sender, instance, **kwargs):
    """Handle Pack deletion."""
    create_automated_event(
        event_type="deleted",
        instance=instance,
        description=f"Pack '{instance.serial_number}' from batch '{instance.batch.lot_number}' was deleted",
        severity="medium",
        metadata={
            "serial_number": instance.serial_number,
            "batch_lot_number": instance.batch.lot_number,
            "product_name": instance.batch.product.name,
            "deleted_fields": {
                "serial_number": instance.serial_number,
                "pack_size": instance.pack_size,
                "pack_type": instance.pack_type,
                "status": instance.status,
                "location": instance.location,
            },
        },
    )


# Shipment signals
@receiver(post_save, sender=m.Shipment)
def shipment_post_save(sender, instance, created, **kwargs):
    """Handle Shipment creation and updates."""
    if created:
        create_automated_event(
            event_type="created",
            instance=instance,
            description=f"Shipment '{instance.tracking_number}' was created",
            metadata={
                "tracking_number": instance.tracking_number,
                "carrier": instance.carrier,
                "service_type": instance.service_type,
                "status": instance.status,
                "origin_name": instance.origin_name,
                "destination_name": instance.destination_name,
            },
        )
    else:
        # Get field changes and check specifically for status changes
        changes = get_field_changes(instance, created=False)

        # Check if status changed specifically
        if "status" in changes and changes["status"].get("old") != changes[
            "status"
        ].get("new"):
            old_status = changes["status"]["old"]
            new_status = changes["status"]["new"]

            # Create specific status change event
            create_status_change_event(instance, old_status, new_status)

        # Create general update event
        create_automated_event(
            event_type="updated",
            instance=instance,
            description=f"Shipment '{instance.tracking_number}' was updated",
            metadata={
                "tracking_number": instance.tracking_number,
                "carrier": instance.carrier,
                "status": instance.status,
                "changes": changes,
            },
        )


@receiver(post_delete, sender=m.Shipment)
def shipment_post_delete(sender, instance, **kwargs):
    """Handle Shipment deletion."""
    create_automated_event(
        event_type="deleted",
        instance=instance,
        description=f"Shipment '{instance.tracking_number}' was deleted",
        severity="medium",
        metadata={
            "tracking_number": instance.tracking_number,
            "carrier": instance.carrier,
            "deleted_fields": {
                "tracking_number": instance.tracking_number,
                "carrier": instance.carrier,
                "service_type": instance.service_type,
                "status": instance.status,
                "origin_name": instance.origin_name,
                "destination_name": instance.destination_name,
            },
        },
    )


# Many-to-many relationship signals for shipments
@receiver(m2m_changed, sender=m.Shipment.packs.through)
def shipment_packs_changed(sender, instance, action, pk_set, **kwargs):
    """Handle changes to shipment-pack relationships."""
    if action == "post_add" and pk_set:
        pack_serials = []
        for pack_id in pk_set:
            try:
                pack = m.Pack.objects.get(id=pack_id)
                pack_serials.append(pack.serial_number)
            except m.Pack.DoesNotExist:
                continue

        if pack_serials:
            create_automated_event(
                event_type="updated",
                instance=instance,
                description=f"Packs added to shipment '{instance.tracking_number}': {', '.join(pack_serials)}",
                metadata={
                    "tracking_number": instance.tracking_number,
                    "action": "packs_added",
                    "pack_serials": pack_serials,
                    "pack_count": len(pack_serials),
                },
            )

    elif action == "post_remove" and pk_set:
        pack_serials = []
        for pack_id in pk_set:
            try:
                pack = m.Pack.objects.get(id=pack_id)
                pack_serials.append(pack.serial_number)
            except m.Pack.DoesNotExist:
                continue

        if pack_serials:
            create_automated_event(
                event_type="updated",
                instance=instance,
                description=f"Packs removed from shipment '{instance.tracking_number}': {', '.join(pack_serials)}",
                metadata={
                    "tracking_number": instance.tracking_number,
                    "action": "packs_removed",
                    "pack_serials": pack_serials,
                    "pack_count": len(pack_serials),
                },
            )


# Custom signal handlers for status changes
def create_status_change_event(instance, old_status, new_status):
    """Create a status_changed event for entities that support status tracking."""
    severity = "info"

    # Determine severity based on status change
    if new_status in ["recalled", "damaged", "lost", "destroyed"]:
        severity = "critical"  # Most serious situations
    elif new_status in ["quarantined", "expired", "cancelled"]:
        severity = "high"  # Serious but not critical
    elif new_status in ["delivered", "shipped", "released"]:
        severity = "info"

    entity_type_map = {
        m.Product: "product",
        m.Batch: "batch",
        m.Pack: "pack",
        m.Shipment: "shipment",
    }

    entity_type = entity_type_map.get(type(instance))
    if not entity_type:
        return

    # Get display name based on entity type
    if hasattr(instance, "name"):
        entity_name = instance.name
    elif hasattr(instance, "tracking_number"):
        entity_name = instance.tracking_number
    elif hasattr(instance, "serial_number"):
        entity_name = instance.serial_number
    elif hasattr(instance, "lot_number"):
        entity_name = instance.lot_number
    else:
        entity_name = f"{entity_type}#{instance.id}"

    create_automated_event(
        event_type="status_changed",
        instance=instance,
        description=f"{entity_type.title()} '{entity_name}' status changed from '{old_status}' to '{new_status}'",
        severity=severity,
        metadata={
            "entity_name": entity_name,
            "old_status": old_status,
            "new_status": new_status,
            "status_change": True,
        },
    )


# Note: To properly track status changes, you would need to modify the model's save() method
# or use a package like django-model-utils that tracks field changes.
# For now, the status change detection is simplified.


# Event signals for blockchain integrity
@receiver(post_save, sender=m.Event)
def event_post_save(sender, instance, created, **kwargs):
    """Handle Event creation and updates - compute hash for blockchain anchoring."""
    if created:
        # Compute and store event hash for new events
        if not instance.event_hash:
            instance.update_event_hash()
        
        # Queue notification processing for the new event
        # Use on_commit to ensure the event is saved to DB before Celery task runs
        from django.db import transaction
        from supplychain.tasks import process_event_notifications

        def queue_notifications():
            try:
                process_event_notifications.delay(instance.id)
            except Exception as notify_error:
                # Log but don't fail if notification queuing fails
                logger.warning(
                    f"Failed to queue notification for event {instance.id}: {notify_error}",
                    exc_info=True
                )
        
        transaction.on_commit(queue_notifications)
    else:
        # Recompute hash if event data was modified (except blockchain fields)
        # This helps detect tampering with event data

        # Check if any non-blockchain fields were updated
        # For now, we'll always recompute the hash when an event is updated
        current_hash = instance.compute_event_hash()
        if instance.event_hash != current_hash:
            # This could indicate tampering or legitimate update
            # For now, just update the hash (in production, you might want to log this)
            instance.event_hash = current_hash
            instance.save(update_fields=["event_hash"])
