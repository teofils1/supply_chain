"""
reset_app.py

Deletes all data from each table in the Django app, preserving the schema.
Usage:
    uv run python src/reset_app.py
"""

import os
import sys

import django
from django.db import transaction

import supplychain.models as m

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
django.setup()


# List all models to clear (order matters for FKs)
MODELS = [
    m.Event,
    m.ShipmentPack,
    m.Shipment,
    m.Pack,
    m.Batch,
    m.Product,
]


def reset_app():
    with transaction.atomic():
        for model in MODELS:
            print(f"Deleting all {model.__name__}...")
            model.objects.all().delete()
    print("All data deleted. App is reset.")


if __name__ == "__main__":
    reset_app()
