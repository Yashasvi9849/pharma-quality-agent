from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.anomaly_detector import detect_anomalies
from src.data_generator import generate_synthetic_batches
from src.deviation_checker import check_process_deviations
from src.documentation_checker import check_missing_documentation
from src.report_generator import generate_csv_report, generate_markdown_report
from src.risk_scorer import calculate_risk_score
from src.root_cause_engine import generate_qa_checklist, generate_root_cause_summary


def load_batch_data(csv_path: str | Path | None = None) -> pd.DataFrame:
    if csv_path:
        data = pd.read_csv(csv_path)
    else:
        data = generate_synthetic_batches()
    return prepare_batch_data(data)


def prepare_batch_data(data: pd.DataFrame) -> pd.DataFrame:
    prepared = data.copy()
    if "timestamp" in prepared.columns:
        prepared["timestamp"] = pd.to_datetime(prepared["timestamp"], errors="coerce")
    return prepared.sort_values(["batch_id", "timestamp"]).reset_index(drop=True)


def analyze_batch(data: pd.DataFrame, batch_id: str) -> dict[str, Any]:
    prepared = prepare_batch_data(data)
    batch = prepared[prepared["batch_id"].astype(str) == str(batch_id)].copy()

    if batch.empty:
        raise ValueError(f"Batch ID not found: {batch_id}")

    batch = detect_anomalies(batch)
    deviations = check_process_deviations(batch)
    missing_docs = check_missing_documentation(batch)
    risk_result = calculate_risk_score(batch, deviations, missing_docs)
    summary = generate_root_cause_summary(batch, deviations, missing_docs, risk_result)
    checklist = generate_qa_checklist(risk_result)

    markdown_report = generate_markdown_report(
        str(batch_id),
        risk_result,
        deviations,
        missing_docs,
        summary,
        checklist,
    )
    csv_report = generate_csv_report(str(batch_id), risk_result, summary, checklist)

    return {
        "batch_id": str(batch_id),
        "risk": risk_result,
        "root_cause_summary": summary,
        "qa_checklist": checklist,
        "process_deviations": _records(deviations),
        "missing_documentation": _records(missing_docs),
        "anomaly_rows": _records(batch[batch["is_anomaly"]]),
        "batch_rows": _records(batch),
        "reports": {
            "markdown": markdown_report,
            "csv": csv_report,
        },
        "dataframes": {
            "batch": batch,
            "deviations": deviations,
            "missing_docs": missing_docs,
        },
    }


def api_result(result: dict[str, Any]) -> dict[str, Any]:
    public_result = {key: value for key, value in result.items() if key != "dataframes"}
    public_result["decision_support_notice"] = (
        "Decision-support only. Human QA approval is required. "
        "The system must never approve a batch automatically."
    )
    return public_result


def _records(data: pd.DataFrame) -> list[dict[str, Any]]:
    if data.empty:
        return []
    serializable = data.copy()
    for column in serializable.columns:
        if pd.api.types.is_datetime64_any_dtype(serializable[column]):
            serializable[column] = serializable[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    return serializable.to_dict(orient="records")
