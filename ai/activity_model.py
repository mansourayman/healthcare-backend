# backend/ai/activity_model.py
import joblib
import numpy as np
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "activity_model.pkl")

class ActivityModel:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)

    def predict(self, features: dict):
        X = np.array([[
            features["heart_rate"],
            features["steps_delta"],
            features["jumps_delta"],
            features["acc_mag_mean"],
            features["acc_mag_std"],
            features["acc_mag_max"]
        ]])

        label = self.model.predict(X)[0]
        confidence = max(self.model.predict_proba(X)[0])

        return {
            "activity": label,
            "confidence": round(float(confidence), 2)
        }
