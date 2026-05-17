import csv
import random

OUTPUT_FILE = "dataset.csv"

# كل كام ثانية السيستم بيسجل (زي ESP32)
INTERVAL_SEC = 20

# المدة بالدقايق (غيرها براحتك: 10 / 30 / 60)
DURATION_MIN = 60

samples = int((DURATION_MIN * 60) / INTERVAL_SEC)

def gen_rest():
    return [
        random.randint(68, 80),     # heart_rate
        0,                           # steps
        0,                           # jumps
        round(random.uniform(0.06, 0.15), 3),
        round(random.uniform(0.01, 0.03), 3),
        round(random.uniform(0.15, 0.30), 3),
        "rest"
    ]

def gen_walking():
    return [
        random.randint(80, 95),
        random.randint(3, 10),
        0,
        round(random.uniform(0.3, 1.0), 3),
        round(random.uniform(0.05, 0.15), 3),
        round(random.uniform(0.8, 1.8), 3),
        "walking"
    ]

def gen_running():
    return [
        random.randint(105, 140),
        random.randint(15, 30),
        random.randint(0, 2),
        round(random.uniform(1.2, 2.3), 3),
        round(random.uniform(0.2, 0.4), 3),
        round(random.uniform(2.5, 4.0), 3),
        "running"
    ]

def gen_jumping():
    return [
        random.randint(100, 130),
        random.randint(1, 5),
        random.randint(2, 5),
        round(random.uniform(2.0, 3.0), 3),
        round(random.uniform(0.4, 0.7), 3),
        round(random.uniform(4.0, 5.5), 3),
        "jumping"
    ]

generators = [
    gen_rest,
    gen_walking,
    gen_running,
    gen_jumping
]

with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "heart_rate",
        "steps_delta",
        "jumps_delta",
        "acc_mag_mean",
        "acc_mag_std",
        "acc_mag_max",
        "label"
    ])

    for i in range(samples):
        gen = random.choice(generators)
        writer.writerow(gen())

print(f"✅ Dataset created: {OUTPUT_FILE}")
print(f"📊 Samples: {samples}")
