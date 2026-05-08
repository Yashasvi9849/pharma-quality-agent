from __future__ import annotations

from io import BytesIO
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from src.data_generator import SENSOR_COLUMNS


API_BASE_URL = os.getenv("PHARMA_API_URL", "http://127.0.0.1:8000").rstrip("/")


st.set_page_config(
    page_title="Pharma Manufacturing Quality Assistant",
    page_icon="QA",
    layout="wide",
)


st.markdown(
    """
    <style>
    :root {
        --qa-blue: #1f6f8b;
        --qa-teal: #0b8f7a;
        --qa-red: #b42318;
        --qa-amber: #b54708;
        --qa-green: #027a48;
        --qa-border: #d9e2ec;
        --qa-bg: #f6f9fb;
    }
    .stApp {
        background: var(--qa-bg);
    }
    .main .block-container {
        padding-top: 2rem;
    }
    .app-header {
        background: linear-gradient(90deg, #ffffff 0%, #eef7f6 100%);
        border: 1px solid var(--qa-border);
        border-radius: 8px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 1rem;
    }
    .app-header h1 {
        margin: 0;
        color: #17324d;
        font-size: 2rem;
        letter-spacing: 0;
    }
    .app-header p {
        margin: .25rem 0 0;
        color: #486581;
        font-size: 1rem;
    }
    .warning-note {
        color: #7a271a;
        background: #fff4ed;
        border: 1px solid #fed7aa;
        border-radius: 8px;
        padding: .75rem 1rem;
        margin-top: .8rem;
        font-weight: 600;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid var(--qa-border);
        border-radius: 8px;
        padding: 1rem;
        min-height: 112px;
        box-shadow: 0 1px 2px rgba(16, 24, 40, .05);
    }
    .kpi-label {
        color: #5f6f7f;
        font-size: .85rem;
        margin-bottom: .45rem;
    }
    .kpi-value {
        color: #17324d;
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .status-banner {
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 1rem 0;
        font-weight: 700;
        border: 1px solid;
    }
    .status-low {
        color: var(--qa-green);
        background: #ecfdf3;
        border-color: #abefc6;
    }
    .status-medium {
        color: var(--qa-amber);
        background: #fffaeb;
        border-color: #fedf89;
    }
    .status-high {
        color: var(--qa-red);
        background: #fef3f2;
        border-color: #fecdca;
    }
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--qa-border);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def request_json(method: str, path: str, **kwargs) -> dict[str, object]:
    url = f"{API_BASE_URL}{path}"
    response = requests.request(method, url, timeout=30, **kwargs)
    response.raise_for_status()
    return response.json()


def batch_options_from_upload(uploaded_file) -> list[str]:
    if uploaded_file is None:
        payload = request_json("GET", "/batches")
        return payload["batch_ids"]

    data = pd.read_csv(BytesIO(uploaded_file.getvalue()))
    if "batch_id" not in data.columns:
        raise ValueError("Uploaded CSV must include a batch_id column.")
    return sorted(data["batch_id"].dropna().astype(str).unique().tolist())


def analyze_batch(uploaded_file, batch_id: str) -> dict[str, object]:
    if uploaded_file is None:
        payload = request_json("GET", f"/analyze/{batch_id}")
    else:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type or "text/csv",
            )
        }
        payload = request_json("POST", "/analyze", data={"batch_id": batch_id}, files=files)

    batch = pd.DataFrame(payload["batch_rows"])
    deviations = pd.DataFrame(payload["process_deviations"])
    missing_docs = pd.DataFrame(payload["missing_documentation"])
    if not batch.empty and "timestamp" in batch.columns:
        batch["timestamp"] = pd.to_datetime(batch["timestamp"], errors="coerce")
    return {
        "batch": batch,
        "deviations": deviations,
        "missing_docs": missing_docs,
        "risk": payload["risk"],
        "summary": payload["root_cause_summary"],
        "checklist": payload["qa_checklist"],
        "reports": payload["reports"],
        "decision_support_notice": payload["decision_support_notice"],
    }


def status_class(risk_level: str) -> str:
    if risk_level.startswith("Low"):
        return "status-low"
    if risk_level.startswith("Medium"):
        return "status-medium"
    return "status-high"


def render_kpi(label: str, value: object) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sensor_chart(batch: pd.DataFrame, sensor: str, title: str):
    fig = px.line(batch, x="timestamp", y=sensor, title=title, markers=True)
    anomalies = batch[batch["is_anomaly"]]
    if not anomalies.empty:
        fig.add_scatter(
            x=anomalies["timestamp"],
            y=anomalies[sensor],
            mode="markers",
            marker={"size": 11, "color": "#b42318", "symbol": "x"},
            name="Anomaly",
        )
    fig.update_layout(
        height=320,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
        paper_bgcolor="white",
        plot_bgcolor="white",
        title_font={"size": 17, "color": "#17324d"},
        legend_orientation="h",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#edf2f7")
    fig.update_yaxes(showgrid=True, gridcolor="#edf2f7")
    return fig


st.markdown(
    """
    <div class="app-header">
        <h1>Pharma Manufacturing Quality Assistant</h1>
        <p>AI-assisted batch risk monitoring for QA review</p>
        <div class="warning-note">Decision-support only. Human QA approval required.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Controls")
    st.caption(f"Backend: {API_BASE_URL}")
    uploaded_csv = st.file_uploader("Upload CSV", type=["csv"])

    try:
        batch_options = batch_options_from_upload(uploaded_csv)
        backend_ready = True
    except (requests.RequestException, ValueError) as exc:
        batch_options = []
        backend_ready = False
        st.error(f"Backend connection failed: {exc}")

    if not batch_options:
        st.stop()

    default_index = batch_options.index("BATCH-010") if "BATCH-010" in batch_options else 0
    selected_batch = st.selectbox("Select Batch ID", batch_options, index=default_index)
    analyze = st.button("Analyze Batch", type="primary", use_container_width=True)
    show_raw = st.toggle("Show Raw Data", value=False)
    show_technical = st.toggle("Show Technical Details", value=False)

if backend_ready and (analyze or selected_batch):
    try:
        result = analyze_batch(uploaded_csv, selected_batch)
    except requests.RequestException as exc:
        st.error(f"Backend analysis request failed: {exc}")
        st.stop()

    batch = result["batch"]
    deviations = result["deviations"]
    missing_docs = result["missing_docs"]
    risk = result["risk"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi("Batch Risk Score", risk["score"])
    with col2:
        render_kpi("Risk Level", risk["risk_level"])
    with col3:
        render_kpi("Number of Sensor Anomalies", risk["anomaly_count"])
    with col4:
        render_kpi("Missing Documentation Count", risk["missing_doc_count"])

    st.markdown(
        f'<div class="status-banner {status_class(risk["risk_level"])}">{risk["risk_level"]}</div>',
        unsafe_allow_html=True,
    )

    chart_a, chart_b = st.columns(2)
    with chart_a:
        st.plotly_chart(sensor_chart(batch, "temperature", "Temperature Trend"), use_container_width=True)
        st.plotly_chart(sensor_chart(batch, "vibration", "Vibration Trend"), use_container_width=True)
    with chart_b:
        st.plotly_chart(sensor_chart(batch, "humidity", "Humidity Trend"), use_container_width=True)
        st.plotly_chart(
            sensor_chart(batch, "compression_force", "Compression Force Trend"),
            use_container_width=True,
        )

    st.subheader("Detected Issues")
    st.caption("Process deviations")
    if deviations.empty:
        st.success("No process-limit deviations detected.")
    else:
        st.dataframe(deviations, use_container_width=True, hide_index=True)

    st.caption("Missing documentation")
    if missing_docs.empty:
        st.success("No missing documentation detected.")
    else:
        st.dataframe(missing_docs, use_container_width=True, hide_index=True)

    st.subheader("Root Cause Summary")
    st.write(result["summary"])

    st.subheader("QA Review Checklist")
    for item in result["checklist"]:
        st.checkbox(item, value=False)
    st.info("This tool cannot approve or release a batch. Final disposition must be made by authorized QA personnel.")

    markdown_report = result["reports"]["markdown"]
    csv_report = result["reports"]["csv"]

    dl_a, dl_b = st.columns(2)
    with dl_a:
        st.download_button(
            "Download Markdown Report",
            markdown_report,
            file_name=f"{selected_batch}_qa_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with dl_b:
        st.download_button(
            "Download CSV Report",
            csv_report,
            file_name=f"{selected_batch}_qa_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if show_raw:
        st.subheader("Raw Data")
        st.dataframe(batch, use_container_width=True, hide_index=True)

    if show_technical:
        st.subheader("Technical Details")
        st.write("Backend URL:", API_BASE_URL)
        st.write("Decision-support notice:", result["decision_support_notice"])
        st.write("Sensor columns:", SENSOR_COLUMNS)
        st.json(risk)
