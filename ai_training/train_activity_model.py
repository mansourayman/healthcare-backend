# ai_training/train_activity_model.py
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier


df = pd.read_csv("dataset.csv")

X = df[
    ["heart_rate", "steps_delta", "jumps_delta",
     "acc_mag_mean", "acc_mag_std", "acc_mag_max"]
]

y = df["label"]  # rest / walking / running / jumping

# الموديل
model = RandomForestClassifier(
    n_estimators=150,
    max_depth=12,
    random_state=42
)

model.fit(X, y)


joblib.dump(model, "activity_model.pkl")

print("Model trained and saved as activity_model.pkl")
