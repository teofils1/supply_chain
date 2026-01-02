"""
Django management command to reset all data in the supply chain app.

This command permanently deletes all data from the app while preserving the schema.
It uses TRUNCATE with CASCADE on PostgreSQL for efficiency, or DELETE on other databases.

Usage:
    python manage.py reset_data
    python manage.py reset_data --force  # Skip confirmation prompt
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection, transaction

import supplychain.models as m

User = get_user_model()


class Command(BaseCommand):
    help = "Reset all data in the supply chain app (delete all records)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip confirmation prompt",
        )
        parser.add_argument(
            "--keep-users",
            action="store_true",
            help="Keep user accounts (only delete supply chain data)",
        )

    def handle(self, *args, **options):
        if not options["force"]:
            confirm = input(
                "\n⚠️  WARNING: This will permanently delete ALL data!\n"
                "Type 'yes' to confirm: "
            )
            if confirm.lower() != "yes":
                self.stdout.write(self.style.ERROR("Operation cancelled."))
                return

        self.stdout.write(self.style.WARNING("Resetting all data..."))

        keep_users = options["keep_users"]

        # Models in dependency order (children first)
        models_to_clear = [
            m.NotificationLog,
            m.NotificationRule,
            m.Document,
            m.Event,
            m.ShipmentPack,
            m.Shipment,
            m.Pack,
            m.Batch,
            m.Product,
            m.RoleAssignment,
            m.UserProfile,
        ]

        with transaction.atomic():
            engine = settings.DATABASES["default"]["ENGINE"].lower()

            if "postgresql" in engine:
                self._truncate_postgres(models_to_clear, keep_users)
            else:
                self._delete_fallback(models_to_clear, keep_users)

        self.stdout.write(self.style.SUCCESS("✓ All data has been reset successfully!"))

        if not keep_users:
            self.stdout.write(
                self.style.SUCCESS("✓ User accounts (except superusers) have been deleted.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✓ User accounts have been preserved.")
            )

    def _truncate_postgres(self, models, keep_users):
        """Use PostgreSQL TRUNCATE for efficient bulk deletion."""
        tables = ", ".join(
            connection.ops.quote_name(model._meta.db_table)
            for model in models
        )

        self.stdout.write(f"Truncating tables: {tables}")

        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE;")

        if not keep_users:
            # Delete non-superuser users
            deleted_count, _ = User.objects.filter(is_superuser=False).delete()
            self.stdout.write(f"Deleted {deleted_count} user accounts")

    def _delete_fallback(self, models, keep_users):
        """Fallback DELETE for non-PostgreSQL databases."""
        with connection.cursor() as cursor:
            for model in models:
                table = connection.ops.quote_name(model._meta.db_table)
                self.stdout.write(f"Deleting all rows from {table}...")
                cursor.execute(f"DELETE FROM {table};")

        if not keep_users:
            deleted_count, _ = User.objects.filter(is_superuser=False).delete()
            self.stdout.write(f"Deleted {deleted_count} user accounts")
