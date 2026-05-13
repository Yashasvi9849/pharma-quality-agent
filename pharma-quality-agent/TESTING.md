# Testing Reference

This guide is for testers who are new to the Pharma Manufacturing Quality Assistant.

## Application Purpose

The application helps QA teams review pharma manufacturing batches. It checks sensor data, process-limit deviations, missing documentation, quality failures, and generates a QA-ready investigation summary.

The application is decision-support only. It must never approve or release a batch automatically.

## Local URLs

```text
React dashboard:    http://127.0.0.1:5173
Streamlit dashboard: http://localhost:8507
Backend API docs:   http://127.0.0.1:8000/docs
Backend health:     http://127.0.0.1:8000/health
```

## Smoke Test

1. Open `http://127.0.0.1:5173`.
2. Confirm the dashboard title appears:
   `Pharma Manufacturing Quality Assistant`
3. Confirm the sidebar shows:
   - Upload CSV
   - Select Batch ID
   - Analyze Batch
   - Show Raw Data
   - Show Technical Details
4. Select `BATCH-010`.
5. Click `Analyze Batch`.

Expected result:

- Risk level is `High Risk, QA Review Required`.
- A high-risk recommendation panel is visible.
- The risk score bar points to the high-risk band.
- Primary risk drivers are listed near the top of the dashboard.
- KPI cards show risk score, risk level, sensor anomalies, and missing documentation count.
- Charts are visible for temperature, humidity, vibration, and compression force.
- Charts include upper/lower process-limit lines and markers for anomalies or out-of-limit readings.
- Detected issues tables are visible.
- Root-cause summary is visible.
- QA checklist is visible.
- Download report buttons are visible.

## Key Test Scenarios

### 1. Low-Risk Batch

Use `BATCH-001`.

Expected:

- Risk level should be `Low Risk`.
- No major process deviations should be shown.
- Missing documentation count should be low or zero.
- The app should still say human QA approval is required.

### 2. Medium-Risk Batch

Use `BATCH-003`, `BATCH-006`, or `BATCH-007`.

Expected:

- Risk level should be `Medium Risk`.
- The detected issue should match the batch pattern, such as humidity drift, compression force drift, or missing review documentation.
- Root-cause summary should explain the issue in plain English.

### 3. High-Risk Batch

Use `BATCH-010`.

Expected:

- Risk level should be `High Risk, QA Review Required`.
- Compression force deviations should appear in the process deviations table.
- Missing `cleaning_verification` should appear in the missing documentation table.
- QA checklist should include human review before batch disposition.

### 4. Uploaded CSV

Use `data/sample_batches.csv`.

Steps:

1. Upload the CSV from the dashboard sidebar.
2. Select `BATCH-010`.
3. Click `Analyze Batch`.

Expected:

- The dashboard should analyze the uploaded data through the backend.
- Results should match the sample-data path.
- No crash should occur.

### 5. Raw Data Toggle

Steps:

1. Turn on `Show Raw Data`.
2. Analyze a batch.

Expected:

- A raw data table appears.
- It includes sensor columns and anomaly fields such as `is_anomaly`.

### 6. Technical Details Toggle

Steps:

1. Turn on `Show Technical Details`.
2. Analyze a batch.

Expected:

- Backend URL is shown.
- Decision-support notice is shown.
- Sensor columns are shown.
- Risk JSON is shown.

### 7. Download Reports

Steps:

1. Analyze `BATCH-010`.
2. Click `Download Markdown Report`.
3. Click `Download CSV Report`.

Expected:

- Markdown report downloads successfully.
- CSV report downloads successfully.
- Reports include risk score, risk level, root-cause summary, detected issues, and QA checklist.

## API Tests

Open `http://127.0.0.1:8000/docs`.

### Health Check

Endpoint:

```text
GET /health
```

Expected:

```json
{
  "status": "ok",
  "notice": "Decision-support only. Human QA approval required."
}
```

### List Batches

Endpoint:

```text
GET /batches
```

Expected:

- Response contains batch IDs.
- `BATCH-010` is included.

### Analyze Sample Batch

Endpoint:

```text
GET /analyze/BATCH-010
```

Expected response includes:

- `risk`
- `root_cause_summary`
- `qa_checklist`
- `process_deviations`
- `missing_documentation`
- `anomaly_rows`
- `batch_rows`
- `reports`
- `decision_support_notice`

### Analyze Uploaded CSV

Endpoint:

```text
POST /analyze
```

Use:

- `batch_id`: `BATCH-010`
- `file`: `data/sample_batches.csv`

Expected:

- Response structure matches `GET /analyze/BATCH-010`.
- Risk level is `High Risk, QA Review Required`.

## Negative Tests

### Invalid Batch ID

Endpoint:

```text
GET /analyze/UNKNOWN-BATCH
```

Expected:

- API returns `404`.
- Error message says the batch ID was not found.

### Invalid Upload

Upload a CSV without a `batch_id` column.

Expected:

- Dashboard shows a clear error.
- App does not crash.

## Pass Criteria

Testing passes if:

- Frontend loads successfully.
- Backend health endpoint returns OK.
- Frontend dropdown is populated from backend data.
- Analyze Batch returns results through the backend.
- Low, medium, and high-risk batches display correct risk bands.
- Charts render with batch time-series data.
- Process deviations and missing documentation are shown when present.
- Root-cause summary is plain English.
- QA checklist is visible.
- Reports download successfully.
- The app never approves or releases a batch automatically.

## Safety Requirement

The app must always communicate:

```text
Decision-support only. Human QA approval required.
```

Any wording that implies automatic approval, automatic rejection, or batch release is a defect.
