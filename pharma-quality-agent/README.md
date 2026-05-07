# Pharma Manufacturing Quality Assistant

Streamlit MVP for AI-assisted pharma manufacturing batch risk monitoring. The app analyzes synthetic or uploaded batch sensor data, flags unusual readings, checks process-limit deviations, identifies incomplete documentation, scores batch risk, and generates a QA review recommendation.

This is decision-support only. The application never approves or releases a batch automatically.

## Problem Statement

Manufacturing quality teams need a fast way to spot process signals that may require review before batch disposition. Sensor drift, equipment instability, missing records, and failed quality results can be scattered across different records. This MVP brings those signals into one simple dashboard for human QA review.

## Why AI Is Useful

The MVP combines deterministic quality rules with an IsolationForest anomaly model. Rule checks catch known process-limit deviations, while anomaly detection helps surface unusual multivariate sensor patterns that may not violate a single limit yet. The output is explainable and deliberately framed as review support, not automated approval.

## How To Run Locally

```bash
cd pharma-quality-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

If no CSV is uploaded, the app generates synthetic sample data automatically.

## Folder Structure

```text
pharma-quality-agent/
  app.py
  requirements.txt
  README.md
  data/
    sample_batches.csv
    sample_batch_records.csv
  src/
    data_generator.py
    anomaly_detector.py
    deviation_checker.py
    documentation_checker.py
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
- The app does not replace GMP controls, quality systems, deviation investigations, or authorized QA disposition.

## Future Agentic AI Upgrade Plan

A later version can convert the modules into coordinated agents using LangGraph:

- Sensor Monitoring Agent: monitors sensor streams and flags unusual patterns.
- Batch Deviation Agent: checks process limits and prioritizes deviations.
- Documentation Agent: verifies batch record completeness and missing evidence.
- Root Cause Agent: synthesizes likely contributors and investigation prompts.
- Human Review Agent: routes high-risk batches to authorized QA reviewers and tracks required decisions.

LangGraph would allow explicit state, traceable handoffs, escalation paths, and human-in-the-loop checkpoints while preserving the core rule that batches are never approved automatically.
