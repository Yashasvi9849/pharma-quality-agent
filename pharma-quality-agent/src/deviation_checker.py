from __future__ import annotations

import pandas as pd


PROCESS_LIMITS = {
    "temperature": (20.0, 25.0),
    "humidity": (30.0, 50.0),
    "pressure": (1.0, 1.5),
    "vibration": (0.0, 0.7),
    "compression_force": (8.0, 10.0),
    "ph": (6.5, 7.5),
}


def check_process_deviations(data: pd.DataFrame) -> pd.DataFrame:
    deviations = []
    for _, row in data.iterrows():
        for field, (lower, upper) in PROCESS_LIMITS.items():
            if field not in data.columns:
                continue
            value = row[field]
            if pd.isna(value) or lower <= float(value) <= upper:
                continue
            deviations.append(
                {
                    "batch_id": row.get("batch_id"),
                    "timestamp": row.get("timestamp"),
                    "field": field,
                    "value": round(float(value), 3),
                    "expected_range": f"{lower:g} to {upper:g}",
                    "severity": _severity(field, float(value), lower, upper),
                }
            )
    return pd.DataFrame(deviations)


def _severity(field: str, value: float, lower: float, upper: float) -> str:
    span = upper - lower
    distance = max(lower - value, value - upper, 0)
    if field in {"vibration", "ph"} or distance > span * 0.2:
        return "High"
    if distance > span * 0.1:
        return "Medium"
    return "Low"
