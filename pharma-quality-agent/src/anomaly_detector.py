from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

from src.data_generator import SENSOR_COLUMNS


def detect_anomalies(
    data: pd.DataFrame,
    contamination: float = 0.08,
    random_state: int = 42,
) -> pd.DataFrame:
    result = data.copy()
    available = [col for col in SENSOR_COLUMNS if col in result.columns]

    if len(result) < 4 or not available:
        result["anomaly_score"] = 0.0
        result["is_anomaly"] = False
        return result

    model = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=random_state,
    )
    features = result[available].astype(float)
    predictions = model.fit_predict(features)
    result["anomaly_score"] = model.decision_function(features)
    result["is_anomaly"] = predictions == -1
    return result
