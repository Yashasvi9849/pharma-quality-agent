from __future__ import annotations

from io import BytesIO
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.pipeline import analyze_batch, api_result, load_batch_data, prepare_batch_data


app = FastAPI(
    title="Agentic AI Pharma Manufacturing Deviation Intelligence System",
    description=(
        "Deterministic backend MVP for pharma manufacturing deviation intelligence. "
        "Decision-support only; human QA approval is always required."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8501",
        "http://localhost:8507",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "notice": "Decision-support only. Human QA approval required.",
    }


@app.get("/batches")
def list_batches() -> dict[str, list[str]]:
    data = load_batch_data()
    return {"batch_ids": sorted(data["batch_id"].astype(str).unique().tolist())}


@app.get("/analyze/{batch_id}")
def analyze_sample_batch(batch_id: str) -> dict[str, object]:
    data = load_batch_data()
    return _analyze_or_404(data, batch_id)


@app.get("/agent/analyze/{batch_id}")
def analyze_sample_batch_with_agents(batch_id: str) -> dict[str, object]:
    data = load_batch_data()
    analysis = _analysis_or_404(data, batch_id)
    return _agent_result(analysis)


@app.post("/analyze")
async def analyze_uploaded_batch(
    batch_id: Annotated[str, Form()],
    file: Annotated[UploadFile | None, File()] = None,
) -> dict[str, object]:
    if file is None:
        data = load_batch_data()
    else:
        contents = await file.read()
        data = pd.read_csv(BytesIO(contents))
        data = prepare_batch_data(data)
    return _analyze_or_404(data, batch_id)


@app.post("/agent/analyze")
async def analyze_uploaded_batch_with_agents(
    batch_id: Annotated[str, Form()],
    file: Annotated[UploadFile | None, File()] = None,
) -> dict[str, object]:
    if file is None:
        data = load_batch_data()
    else:
        contents = await file.read()
        data = pd.read_csv(BytesIO(contents))
        data = prepare_batch_data(data)
    analysis = _analysis_or_404(data, batch_id)
    return _agent_result(analysis)


def _analyze_or_404(data: pd.DataFrame, batch_id: str) -> dict[str, object]:
    return api_result(_analysis_or_404(data, batch_id))


def _analysis_or_404(data: pd.DataFrame, batch_id: str) -> dict[str, object]:
    try:
        return analyze_batch(data, batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _agent_result(analysis: dict[str, object]) -> dict[str, object]:
    risk = analysis["risk"]
    deviations = analysis["process_deviations"]
    missing_docs = analysis["missing_documentation"]
    top_deviation = _top_deviation_driver(deviations)
    missing_fields = [doc["field"].replace("_", " ") for doc in missing_docs]

    steps = [
        {
            "agent": "Sensor Monitoring Agent",
            "status": "complete",
            "finding": (
                f"{risk['anomaly_count']} anomalous sensor reading(s) detected."
                if risk["anomaly_count"]
                else "No anomalous sensor readings detected."
            ),
        },
        {
            "agent": "Batch Deviation Agent",
            "status": "complete",
            "finding": (
                f"{risk['deviation_count']} process deviation(s) found"
                + (f", led by {top_deviation}." if top_deviation else ".")
            ),
        },
        {
            "agent": "Documentation Agent",
            "status": "complete",
            "finding": (
                f"Missing documentation field(s): {', '.join(missing_fields)}."
                if missing_fields
                else "Required documentation fields appear complete."
            ),
        },
        {
            "agent": "Root Cause Agent",
            "status": "complete",
            "finding": analysis["root_cause_summary"],
        },
        {
            "agent": "Human Review Agent",
            "status": "complete",
            "finding": (
                "QA review is required before disposition. The system cannot approve a batch."
            ),
        },
    ]

    return {
        "batch_id": analysis["batch_id"],
        "risk": risk,
        "agent_steps": steps,
        "agent_summary": (
            f"{analysis['batch_id']} is classified as {risk['risk_level']} with a "
            f"risk score of {risk['score']}/100. {analysis['root_cause_summary']}"
        ),
        "recommended_questions": [
            "Which deviation should QA review first?",
            "Which timestamps are most concerning?",
            "What documentation must be completed?",
        ],
        "decision_support_notice": (
            "Decision-support only. Human QA approval is required. "
            "The system must never approve a batch automatically."
        ),
    }


def _top_deviation_driver(deviations: list[dict[str, object]]) -> str:
    counts: dict[str, int] = {}
    for deviation in deviations:
        field = str(deviation.get("field", ""))
        counts[field] = counts.get(field, 0) + 1
    if not counts:
        return ""
    field, count = sorted(counts.items(), key=lambda item: item[1], reverse=True)[0]
    return f"{field.replace('_', ' ')} ({count} reading(s))"
