from __future__ import annotations

import pandas as pd


REQUIRED_DOCUMENTATION_FIELDS = [
    "operator_log",
    "supervisor_review",
    "cleaning_verification",
    "deviation_reason",
]


def check_missing_documentation(data: pd.DataFrame) -> pd.DataFrame:
    issues = []
    for field in REQUIRED_DOCUMENTATION_FIELDS:
        if field not in data.columns:
            issues.append(
                {
                    "field": field,
                    "status": "Missing column",
                    "detail": "Required documentation field is absent from the dataset.",
                }
            )
            continue

        values = data[field].fillna("").astype(str).str.strip()
        missing_count = int((values == "").sum())
        if missing_count:
            issues.append(
                {
                    "field": field,
                    "status": "Incomplete",
                    "detail": f"{missing_count} row(s) missing required documentation.",
                }
            )
    return pd.DataFrame(issues)
