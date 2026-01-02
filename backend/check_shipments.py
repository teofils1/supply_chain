#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/app/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from supplychain.models import Shipment
from django.utils import timezone
from datetime import timedelta

# Check shipments in the last 30 days
end_date = timezone.now()
start_date = end_date - timedelta(days=30)
shipments = Shipment.objects.filter(created_at__gte=start_date, created_at__lte=end_date)

print(f'Total shipments in last 30 days: {shipments.count()}')
print(f'Damaged shipments: {shipments.filter(status="damaged").count()}')
print(f'Lost shipments: {shipments.filter(status="lost").count()}')
print()

for carrier in ['fedex', 'ups', 'dhl', 'usps', 'local', 'internal']:
    carrier_shipments = shipments.filter(carrier=carrier)
    damaged = carrier_shipments.filter(status='damaged').count()
    lost = carrier_shipments.filter(status='lost').count()
    total = carrier_shipments.count()
    damage_rate = (damaged / total * 100) if total > 0 else 0
    loss_rate = (lost / total * 100) if total > 0 else 0
    print(f'{carrier}: total={total}, damaged={damaged} ({damage_rate:.2f}%), lost={lost} ({loss_rate:.2f}%)')

# Check all shipments
print()
print('All shipments:')
all_shipments = Shipment.objects.all()
print(f'Total: {all_shipments.count()}')
print(f'Damaged: {all_shipments.filter(status="damaged").count()}')
print(f'Lost: {all_shipments.filter(status="lost").count()}')
