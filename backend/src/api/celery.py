"""
Celery configuration for the Supply Chain API.

This module configures Celery with RabbitMQ as the message broker.
"""

import os

# Set the default Django settings module BEFORE importing Django or Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

# Setup Django BEFORE Celery to avoid circular import issues with Django 5+
import django

django.setup()

from celery import Celery

# Create the Celery application WITHOUT fixups
app = Celery("api", fixups=[])

# Load config from Django settings, using the CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Fix for Celery 5.4+ bug with Django fixup
# Explicitly set the worker pool to avoid AttributeError
app.conf.worker_pool = "solo"

# Auto-discover tasks in all registered Django apps
# Since fixups are disabled, we need to explicitly provide the list
app.autodiscover_tasks(lambda: ["supplychain"])


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
