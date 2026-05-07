from __future__ import annotations

import pandas as pd

from src.documentation_checker import REQUIRED_DOCUMENTATION_FIELDS


def calculate_risk_score(
    batch_data: pd.DataFrame,
    deviations: pd.DataFrame,
    missing_docs: pd.DataFrame,
) -> dict[str, object]:
    row_count = max(len(batch_data), 1)
    anomaly_count = int(batch_data.get("is_anomaly", pd.Series(dtype=bool)).sum())
    anomaly_ratio = min(anomaly_count / row_count / 0.15, 1.0)

    deviation_ratio = min(len(deviations) / max(row_count * 0.35, 1), 1.0)
    missing_doc_ratio = min(len(missing_docs) / len(REQUIRED_DOCUMENTATION_FIELDS), 1.0)

    quality_failure = 0
    if "quality_result" in batch_data.columns:
        quality_failure = int(
            batch_data["quality_result"].fillna("").astype(str).str.lower().eq("fail").any()
        )

    score = (
        anomaly_ratio * 35
        + deviation_ratio * 35
        + missing_doc_ratio * 20
        + quality_failure * 10
    )
    score = int(round(min(max(score, 0), 100)))
    return {
        "score": score,
        "risk_level": risk_band(score),
        "anomaly_count": anomaly_count,
        "deviation_count": int(len(deviations)),
        "missing_doc_count": int(len(missing_docs)),
        "quality_failure": bool(quality_failure),
    }


def risk_band(score: int | float) -> str:
    if score <= 30:
        return "Low Risk"
    if score <= 65:
        return "Medium Risk"
    return "High Risk, QA Review Required"
