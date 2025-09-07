"""
reset_app.py

Permanently deletes all rows from each table in the Django app, preserving the schema.
Usage:
    uv run python src/reset_app.py
"""

import os
import sys

import django
from django.conf import settings
from django.db import connection, transaction

# Setup Django
# ensure project src is on sys.path
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
django.setup()

import supplychain.models as m

# List all models to clear (order given for reference; TRUNCATE CASCADE ignores order)
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
        engine = settings.DATABASES["default"]["ENGINE"].lower()
        if "postgresql" in engine:
            # Use a single TRUNCATE for all tables to permanently remove rows and reset sequences
            tables = ", ".join(
                connection.ops.quote_name(model._meta.db_table) for model in MODELS
            )
            print(f"Truncating tables: {tables}")
            with connection.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE;")
        else:
            # Fallback: raw DELETE from each table (bypasses Django model delete overrides)
            with connection.cursor() as cursor:
                for model in MODELS:
                    table = connection.ops.quote_name(model._meta.db_table)
                    print(f"Deleting all rows from {table} (raw SQL)...")
                    cursor.execute(f"DELETE FROM {table};")
    print("All data permanently deleted. App is reset.")


if __name__ == "__main__":
    reset_app()
