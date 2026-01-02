#!/usr/bin/env python
import random

carrier_damage_rates = {
    "fedex": 0.03,
    "ups": 0.015,
    "dhl": 0.04,
    "usps": 0.05,
    "local": 0.06,
    "internal": 0.025,
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

# Simulate creating shipments like in seed_data.py
results = {"delivered": 0, "damaged": 0, "lost": 0, "other": 0}
for i in range(200):
    carrier = random.choice(list(carrier_damage_rates.keys()))
    base_status = random.choice(statuses)
    
    # Apply carrier-specific damage rate only to shipments that would otherwise be delivered
    if base_status == "delivered":
        damage_rate = carrier_damage_rates.get(carrier, 0.015)
        loss_rate = damage_rate * 0.2
        
        rand = random.random()
        if rand < loss_rate:
            status = "lost"
        elif rand < (loss_rate + damage_rate):
            status = "damaged"
        else:
            status = "delivered"
    else:
        status = base_status
    
    if status == "delivered":
        results["delivered"] += 1
    elif status == "damaged":
        results["damaged"] += 1
        print(f"Shipment {i}: carrier={carrier}, base={base_status}, final=damaged, rand={rand:.4f}, threshold={loss_rate + damage_rate:.4f}")
    elif status == "lost":
        results["lost"] += 1
        print(f"Shipment {i}: carrier={carrier}, base={base_status}, final=lost, rand={rand:.4f}, threshold={loss_rate:.4f}")
    else:
        results["other"] += 1

print(f"\nResults: {results}")
print(f"Damage rate: {results['damaged'] / 200 * 100:.2f}%")
print(f"Loss rate: {results['lost'] / 200 * 100:.2f}%")
