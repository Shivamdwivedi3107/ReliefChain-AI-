import csv
import random
import os

DISASTER_TYPES = ["flood", "earthquake", "cyclone", "wildfire", "landslide", "tsunami"]

def generate_sample(i: int):
    dtype = random.choice(DISASTER_TYPES)
    people = random.choices(
        [random.randint(1, 4), random.randint(5, 15), random.randint(16, 50), random.randint(51, 300)],
        weights=[0.35, 0.35, 0.20, 0.10]
    )[0]
    loc_risk = round(random.uniform(1.0, 10.0), 2)
    medical = random.choices([0, 1], weights=[0.65, 0.35])[0]
    water = random.choices([0, 1], weights=[0.40, 0.60])[0]
    food = random.choices([0, 1], weights=[0.45, 0.55])[0]
    vulnerable = random.choices([0, 1], weights=[0.60, 0.40])[0]
    time_elapsed = round(random.uniform(0.1, 72.0), 1)

    # Priority determination logic
    score = 0.0
    if dtype in ["earthquake", "tsunami"]:
        score += 3.5
    elif dtype in ["flood", "cyclone"]:
        score += 3.0
    else:
        score += 2.0

    score += min(people / 10.0, 5.0)
    score += 4.5 if medical else 0.0
    score += 2.5 if water else 0.0
    score += 1.5 if food else 0.0
    score += 3.0 if vulnerable else 0.0
    score += loc_risk * 0.4
    score += min(time_elapsed * 0.05, 2.0)

    # Add slight realistic noise
    score += random.uniform(-0.5, 0.5)

    if score >= 13.0 or (medical and people >= 15):
        priority = "critical"
    elif score >= 9.0:
        priority = "high"
    elif score >= 5.5:
        priority = "medium"
    else:
        priority = "low"

    return {
        "id": f"REQ-{10000 + i}",
        "disaster_type": dtype,
        "affected_people": people,
        "location_risk_score": loc_risk,
        "medical_needed": medical,
        "water_needed": water,
        "food_needed": food,
        "vulnerable_population": vulnerable,
        "time_elapsed_hours": time_elapsed,
        "priority": priority,
    }

def main():
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    csv_path = os.path.join(os.path.dirname(__file__), "disaster_relief_requests.csv")
    
    fieldnames = [
        "id", "disaster_type", "affected_people", "location_risk_score",
        "medical_needed", "water_needed", "food_needed", "vulnerable_population",
        "time_elapsed_hours", "priority"
    ]
    
    samples = [generate_sample(i) for i in range(1, 1501)]
    
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(samples)
    
    print(f"Generated {len(samples)} realistic disaster triage records at {csv_path}")

if __name__ == "__main__":
    main()
