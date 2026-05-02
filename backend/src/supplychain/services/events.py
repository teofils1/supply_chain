from typing import Any, Dict, Tuple, Optional
from django.db import models

def get_model_changes(old_instance: models.Model, new_instance: models.Model) -> Dict[str, Dict[str, Any]]:
    """
    Compare old and new model instances and return a dictionary of changes.
    """
    changes = {}
    if not old_instance or not new_instance:
         return changes
         
    for field in old_instance._meta.fields:
        field_name = field.name
        old_value = getattr(old_instance, field_name)
        new_value = getattr(new_instance, field_name)
        
        if old_value != new_value:
            changes[field_name] = {
                "old": old_value,
                "new": new_value
            }
            
    return changes

def get_event_type_for_changes(entity_name: str, changes: Dict[str, Any]) -> str:
    """
    Determine the most specific EVENT_TYPE based on the entity and its field changes.
    """
    if entity_name.lower() == "batch":
        if "status" in changes:
            new_status = changes["status"]["new"].lower()
            if new_status == "released":
                return "batch_released"
            elif new_status == "quarantined":
                return "batch_quarantined"
            elif new_status == "recalled":
                return "batch_recalled"
        if "quality_control_passed" in changes:
            return "quality_control_passed" if changes["quality_control_passed"]["new"] else "quality_control_failed"
            
    if entity_name.lower() == "shipment":
        if "status" in changes:
            new_status = changes["status"]["new"].lower()
            if new_status == "dispatched":
                return "shipment_dispatched"
            elif new_status == "in_transit":
                return "shipment_in_transit"
            elif new_status == "delayed":
                return "shipment_delayed"
            elif new_status == "delivered":
                return "shipment_delivered"
                
    if "storage_temperature" in changes or "temperature" in changes:
        return "temperature_deviation"
        
    if "location" in changes or "manufacturing_location" in changes:
        return "location_transfer"

    if "quantity" in changes:
        return "inventory_adjustment"

    return "configuration_changed"

def generate_event_details_for_update(
    entity_name: str,
    entity_identifier: str,
    old_instance: Optional[models.Model],
    new_instance: models.Model
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generates a specific event type, a descriptive string, and metadata dict containing state deltas.
    
    Args:
        entity_name: Name of the entity (e.g., 'Batch', 'Shipment')
        entity_identifier: Identifier for the entity (e.g., lot number, ID)
        old_instance: The model instance before the update
        new_instance: The model instance after the update
        
    Returns:
        Tuple of (event_type, description, metadata)
    """
    if old_instance is None:
        event_type = f"{entity_name.lower()}_created"
        # Fallback if specific created enum isn't there
        return event_type, f"{entity_name} {entity_identifier} was created.", {}

    changes = get_model_changes(old_instance, new_instance)
    
    if not changes:
        return "configuration_changed", f"{entity_name} {entity_identifier} was updated, but no fields changed.", {}
        
    event_type = get_event_type_for_changes(entity_name, changes)
        
    # Generate human-readable description for specific important fields or fallback to generic
    description_parts = []
    for field, values in changes.items():
        old_val = values['old']
        new_val = values['new']
        
        if field == "status":
            description_parts.append(f"status transitioned from '{old_val}' to '{new_val}'")
        elif field in ["storage_temperature", "temperature"]:
            description_parts.append(f"temperature shifted from {old_val}°C to {new_val}°C")
        elif field in ["quantity", "available_quantity"]:
            diff = (new_val or 0) - (old_val or 0)
            direction = "increased" if diff > 0 else "decreased"
            description_parts.append(f"inventory level {direction} by {abs(diff)} (from {old_val} to {new_val})")
        elif field in ["location", "manufacturing_location", "current_location", "destination"]:
            old_loc = old_val or "an unknown location"
            new_loc = new_val or "an unknown location"
            description_parts.append(f"transferred from '{old_loc}' to '{new_loc}'")
        elif field == "quality_control_passed":
            state = "PASSED" if new_val else "FAILED"
            description_parts.append(f"quality control inspection marked as {state}")
        elif field == "quality_control_notes":
            description_parts.append("quality control notes were updated")
        else:
            # Provide more context even for generic fields if they are simple printable types
            if isinstance(old_val, (str, int, float, bool)) and getattr(new_val, '__class__', None) in (str, int, float, bool, type(None)):
                description_parts.append(f"{field.replace('_', ' ')} changed from '{old_val}' to '{new_val}'")
            else:
                description_parts.append(f"{field.replace('_', ' ')} was updated")

    # Combine description parts
    if description_parts:
        action_desc = ", ".join(description_parts)
        description = f"{entity_name} {entity_identifier}: {action_desc}."
    else:
        description = f"{entity_name} {entity_identifier} was updated."

    metadata = {"changes": changes}
    
    return event_type, description, metadata
