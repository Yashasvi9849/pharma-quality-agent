from __future__ import annotations

from io import BytesIO
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from src.pipeline import analyze_batch, api_result, load_batch_data, prepare_batch_data


app = FastAPI(
    title="Agentic AI Pharma Manufacturing Deviation Intelligence System",
    description=(
        "Deterministic backend MVP for pharma manufacturing deviation intelligence. "
        "Decision-support only; human QA approval is always required."
    ),
    version="0.1.0",
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


def _analyze_or_404(data: pd.DataFrame, batch_id: str) -> dict[str, object]:
    try:
        return api_result(analyze_batch(data, batch_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
