import random

carrier_damage_rates = {
    "fedex": 0.01,   # 1% damage rate
    "ups": 0.005,    # 0.5% damage rate (most reliable)
    "dhl": 0.015,    # 1.5% damage rate
    "usps": 0.02,    # 2% damage rate
    "local": 0.025,  # 2.5% damage rate
    "internal": 0.01, # 1% damage rate
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

# Simulate 1000 shipments
results = {"delivered": 0, "damaged": 0, "lost": 0, "other": 0}
carrier_results = {}

for carrier in carrier_damage_rates.keys():
    carrier_results[carrier] = {"total": 0, "delivered": 0, "damaged": 0, "lost": 0}

for i in range(1000):
    carrier = random.choice(list(carrier_damage_rates.keys()))
    base_status = random.choice(statuses)
    
    # Apply carrier-specific damage rate only to shipments that would otherwise be delivered
    if base_status == "delivered":
        damage_rate = carrier_damage_rates.get(carrier, 0.015)
        loss_rate = damage_rate * 0.2  # Loss rate is typically 20% of damage rate
        
        rand = random.random()
        if rand < loss_rate:
            status = "lost"
        elif rand < (loss_rate + damage_rate):
            status = "damaged"
        else:
            status = "delivered"
    else:
        status = base_status
    
    # Track results
    carrier_results[carrier]["total"] += 1
    if status == "delivered":
        results["delivered"] += 1
        carrier_results[carrier]["delivered"] += 1
    elif status == "damaged":
        results["damaged"] += 1
        carrier_results[carrier]["damaged"] += 1
    elif status == "lost":
        results["lost"] += 1
        carrier_results[carrier]["lost"] += 1
    else:
        results["other"] += 1

print("Overall results (1000 shipments):")
print(f"  Delivered: {results['delivered']}")
print(f"  Damaged: {results['damaged']}")
print(f"  Lost: {results['lost']}")
print(f"  Other: {results['other']}")
print()

print("By carrier:")
for carrier, stats in carrier_results.items():
    damage_rate_pct = (stats['damaged'] / stats['total'] * 100) if stats['total'] > 0 else 0
    loss_rate_pct = (stats['lost'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"{carrier}: total={stats['total']}, damaged={stats['damaged']} ({damage_rate_pct:.2f}%), lost={stats['lost']} ({loss_rate_pct:.2f}%)")
