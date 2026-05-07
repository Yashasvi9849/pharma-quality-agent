from __future__ import annotations

import pandas as pd


def generate_markdown_report(
    batch_id: str,
    risk_result: dict[str, object],
    deviations: pd.DataFrame,
    missing_docs: pd.DataFrame,
    root_cause_summary: str,
    checklist: list[str],
) -> str:
    lines = [
        f"# QA Review Report: {batch_id}",
        "",
        "Decision-support only. Human QA approval is required.",
        "",
        f"**Risk Score:** {risk_result['score']}",
        f"**Risk Level:** {risk_result['risk_level']}",
        f"**Sensor Anomalies:** {risk_result['anomaly_count']}",
        f"**Process Deviations:** {risk_result['deviation_count']}",
        f"**Missing Documentation Items:** {risk_result['missing_doc_count']}",
        "",
        "## Root Cause Summary",
        root_cause_summary,
        "",
        "## QA Checklist",
    ]
    lines.extend([f"- {item}" for item in checklist])

    lines.extend(["", "## Process Deviations"])
    if deviations.empty:
        lines.append("No process deviations detected.")
    else:
        lines.append(deviations.to_markdown(index=False))

    lines.extend(["", "## Missing Documentation"])
    if missing_docs.empty:
        lines.append("No missing documentation detected.")
    else:
        lines.append(missing_docs.to_markdown(index=False))

    return "\n".join(lines)


def generate_csv_report(
    batch_id: str,
    risk_result: dict[str, object],
    root_cause_summary: str,
    checklist: list[str],
) -> str:
    report = pd.DataFrame(
        [
            {
                "batch_id": batch_id,
                "risk_score": risk_result["score"],
                "risk_level": risk_result["risk_level"],
                "sensor_anomalies": risk_result["anomaly_count"],
                "process_deviations": risk_result["deviation_count"],
                "missing_documentation": risk_result["missing_doc_count"],
                "quality_failure": risk_result["quality_failure"],
                "root_cause_summary": root_cause_summary,
                "qa_checklist": " | ".join(checklist),
            }
        ]
    )
    return report.to_csv(index=False)
