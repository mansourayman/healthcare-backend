# backend/ai/health_risk.py
def assess_health_risk(data: dict):
    hr = data.get("heart_rate")
    spo2 = data.get("spo2")
    temp = data.get("temperature_c")
    acc_mean = data.get("acc_mag_mean")
    jumps = data.get("jumps_delta")

    risk = "normal"
    reasons = []

    def set_risk(level: str):
        nonlocal risk
        order = {"normal": 0, "fatigue": 1, "danger": 2}
        if order[level] > order[risk]:
            risk = level

    # Heart rate rules
    if hr is not None:
        if hr >= 140:
            set_risk("danger")
            reasons.append(f"Critical heart rate: {hr} bpm")
        elif hr > 120 and acc_mean is not None and acc_mean < 0.4:
            set_risk("fatigue")
            reasons.append("High heart rate with low movement")

    # SpO2 rules
    if spo2 is not None and spo2 <= 88:
        set_risk("danger")
        reasons.append(f"Critical SpO2 level: {spo2}%")

    # Temperature rules
    if temp is not None:
        if temp >= 39:
            set_risk("danger")
            reasons.append(f"Critical high temperature: {temp} C")
        elif temp >= 37.5:
            set_risk("fatigue")
            reasons.append(f"High temperature: {temp} C")
        elif temp < 35:
            set_risk("danger")
            reasons.append(f"Low temperature: {temp} C")

    # Motion / fall-like signal
    if jumps is not None and jumps >= 5:
        set_risk("danger")
        reasons.append("Abnormal movement or fall detected")

    return {
        "risk_level": risk,
        "reason": "; ".join(reasons) if reasons else None
    }
