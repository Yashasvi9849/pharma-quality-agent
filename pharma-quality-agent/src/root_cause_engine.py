from __future__ import annotations

import pandas as pd


def generate_root_cause_summary(
    batch_data: pd.DataFrame,
    deviations: pd.DataFrame,
    missing_docs: pd.DataFrame,
    risk_result: dict[str, object],
) -> str:
    reasons = []

    if not deviations.empty:
        fields = deviations["field"].value_counts()
        top_field = fields.index[0]
        if top_field == "humidity":
            reasons.append("humidity drift outside the validated process range")
        elif top_field == "vibration":
            reasons.append("vibration spikes that may indicate equipment instability")
        elif top_field == "compression_force":
            reasons.append("compression force drift that may affect tablet consistency")
        else:
            reasons.append(f"{top_field.replace('_', ' ')} measurements outside limits")

    anomaly_count = int(risk_result.get("anomaly_count", 0))
    if anomaly_count:
        reasons.append(f"{anomaly_count} sensor reading(s) flagged as unusual by the anomaly model")

    if not missing_docs.empty:
        missing = ", ".join(missing_docs["field"].str.replace("_", " ").tolist())
        reasons.append(f"incomplete batch documentation for {missing}")

    if risk_result.get("quality_failure"):
        reasons.append("a recorded quality result failure")

    if not reasons:
        return (
            "No major risk pattern was detected. The batch appears consistent with expected "
            "sensor behavior and required documentation is complete, pending normal QA review."
        )

    return (
        "The batch risk appears to be driven by "
        + "; ".join(reasons)
        + ". QA should review the affected records before any disposition decision."
    )


def generate_qa_checklist(risk_result: dict[str, object]) -> list[str]:
    checklist = [
        "Review process deviations and confirm affected timestamps.",
        "Verify batch record completeness.",
        "Check maintenance history for the related equipment.",
        "Confirm whether deviation investigation is required.",
    ]
    if risk_result.get("risk_level") == "High Risk, QA Review Required":
        checklist.append("Human QA review required before batch disposition.")
    else:
        checklist.append("Human QA approval is still required before batch disposition.")
    return checklist
