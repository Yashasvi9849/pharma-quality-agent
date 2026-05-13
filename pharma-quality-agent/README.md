# Agentic AI Pharma Manufacturing Deviation Intelligence System

Backend-first MVP with a React review dashboard for pharma manufacturing deviation intelligence. The system analyzes batch manufacturing data, detects sensor anomalies and process-limit breaches, checks missing documentation, calculates batch risk, and generates a QA-ready investigation summary for human review.

This is decision-support only. The system must never approve, reject, release, or disposition a batch automatically.

## Problem Statement

Pharmaceutical manufacturing teams need to produce every batch within strict quality and compliance limits. During production, sensor data such as temperature, humidity, pressure, vibration, and compression force is continuously generated. However, quality teams often review deviations manually by checking dashboards, batch logs, historical patterns, and documentation records.

This manual process can be slow, repetitive, and error-prone, especially when small signals across multiple sensors together indicate a larger manufacturing risk.

## Project Problem

Build a backend system that analyzes pharma manufacturing batch data, detects process deviations, identifies possible quality risks, checks missing documentation, and generates a QA-ready investigation summary for human review.

## Core Problem In Simple Words

When a medicine batch is being manufactured, something may go slightly wrong, such as humidity drifting, vibration increasing, or compression force becoming unstable.

The system should answer:

```text
Is this batch normal or risky?
What went wrong?
Which sensor or process caused the issue?
Is any documentation missing?
What should QA review before releasing the batch?
```

## Why This Matters

In pharma manufacturing, even small process deviations can affect product quality, safety, and compliance. The goal is not to let AI approve or reject a batch. The goal is to help QA teams investigate faster and more accurately.

## Backend MVP Goal

The deterministic backend supports:

```text
1. Upload or read batch manufacturing data
2. Analyze sensor values
3. Detect anomalies and threshold breaches
4. Calculate batch risk score
5. Identify missing documentation fields
6. Generate final deviation summary
7. Return results through an API
```

## Why AI Is Useful

The MVP combines deterministic quality rules with a scikit-learn IsolationForest anomaly model. Rule checks catch known process-limit deviations, while anomaly detection helps surface unusual multivariate sensor patterns that may not violate a single limit yet. The output is explainable and deliberately framed as review support, not automated approval.

## How To Run Locally

```bash
cd pharma-quality-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the backend API:

```bash
uvicorn api:app --reload
```

Open API docs:

```text
http://localhost:8000/docs
```

Run the React dashboard:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The older Streamlit dashboard is still available for comparison:

```bash
streamlit run app.py
```

If no CSV is uploaded, the app generates synthetic sample data automatically.

## API Endpoints

```text
GET /health
GET /batches
GET /analyze/{batch_id}
POST /analyze
```

Example sample-data request:

```bash
curl http://localhost:8000/analyze/BATCH-010
```

Example CSV upload request:

```bash
curl -X POST http://localhost:8000/analyze \
  -F "batch_id=BATCH-010" \
  -F "file=@data/sample_batches.csv"
```

API responses include:

- Risk score and risk level
- Sensor anomaly rows
- Process deviations
- Missing documentation fields
- Root-cause summary
- QA review checklist
- Markdown and CSV report content
- Decision-support notice

## Folder Structure

```text
pharma-quality-agent/
  api.py
  app.py
  requirements.txt
  README.md
  TESTING.md
  data/
    sample_batches.csv
    sample_batch_records.csv
    test_upload_batches.csv
  frontend/
    index.html
    package.json
    src/
      main.jsx
      styles.css
  src/
    data_generator.py
    analyzer_agent.py
    anomaly_detector.py
    deviation_checker.py
    documentation_checker.py
    pipeline.py
    risk_scorer.py
    root_cause_engine.py
    report_generator.py
```

## Sample Screenshots

Placeholder: dashboard overview screenshot.

Placeholder: high-risk batch review screenshot.

## Data Columns

The core batch data includes `batch_id`, `machine_id`, `timestamp`, sensor columns, documentation fields, maintenance history, and `quality_result`.

Process limits:

| Field | Lower | Upper |
| --- | ---: | ---: |
| temperature | 20 | 25 |
| humidity | 30 | 50 |
| pressure | 1.0 | 1.5 |
| vibration | 0.0 | 0.7 |
| compression_force | 8 | 10 |
| ph | 6.5 | 7.5 |

## Risk Scoring

Risk score is returned from 0 to 100:

- Sensor anomalies: 35%
- Process deviations: 35%
- Missing documentation: 20%
- Quality result failure: 10%

Risk bands:

- 0-30: Low Risk
- 31-65: Medium Risk
- 66-100: High Risk, QA Review Required

## Limitations

- Uses synthetic data by default.
- No external APIs or live manufacturing system connections.
- IsolationForest output depends on available data distribution.
- Root-cause summaries are rule-based plain-English summaries, not validated investigations.
- The API and dashboard do not replace GMP controls, quality systems, deviation investigations, or authorized QA disposition.

## Future Agentic AI Upgrade Plan

The first backend version is intentionally deterministic. A later version can convert the modules into coordinated agents using LangGraph:

- Sensor Monitoring Agent: monitors sensor streams and flags unusual patterns.
- Batch Deviation Agent: checks process limits and prioritizes deviations.
- Documentation Agent: verifies batch record completeness and missing evidence.
- Root Cause Agent: synthesizes likely contributors and investigation prompts.
- Human Review Agent: routes high-risk batches to authorized QA reviewers and tracks required decisions.

LangGraph would allow explicit state, traceable handoffs, escalation paths, and human-in-the-loop checkpoints while preserving the core rule that batches are never approved automatically.
