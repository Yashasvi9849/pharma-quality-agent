import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  ClipboardCheck,
  Database,
  Download,
  FileSearch,
  Gauge,
  LineChart,
  ListChecks,
  RotateCw,
  Upload,
} from "lucide-react";
import manufacturingBg from "./assets/pharma-manufacturing-bg.png";
import pillAccent from "./assets/pill-accent.png";
import "./styles.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const SENSOR_LIMITS = {
  temperature: [20, 25],
  humidity: [30, 50],
  pressure: [1.0, 1.5],
  vibration: [0.0, 0.7],
  compression_force: [8, 10],
  ph: [6.5, 7.5],
};

const SENSOR_LABELS = {
  temperature: "Temperature",
  humidity: "Humidity",
  vibration: "Vibration",
  compression_force: "Compression Force",
};

function App() {
  const [backendOk, setBackendOk] = useState(false);
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState("BATCH-010");
  const [activeTab, setActiveTab] = useState("dashboard");
  const [uploadedFile, setUploadedFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [rawOpen, setRawOpen] = useState(false);
  const [technicalOpen, setTechnicalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [agentRun, setAgentRun] = useState(false);
  const [agentLoading, setAgentLoading] = useState(false);
  const [agentSummary, setAgentSummary] = useState(null);
  const [agentAnswer, setAgentAnswer] = useState("");

  useEffect(() => {
    refreshBatches();
  }, []);

  async function api(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, options);
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed with ${response.status}`);
    }
    return response.json();
  }

  async function refreshBatches() {
    try {
      setError("");
      const health = await api("/health");
      setBackendOk(health.status === "ok");
      const payload = await api("/batches");
      setBatches(payload.batch_ids);
      if (payload.batch_ids.includes("BATCH-010")) {
        setSelectedBatch("BATCH-010");
      } else if (payload.batch_ids.length) {
        setSelectedBatch(payload.batch_ids[0]);
      }
    } catch (err) {
      setBackendOk(false);
      setError(`Backend unavailable: ${err.message}`);
    }
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0] || null;
    setUploadedFile(file);
    setAnalysis(null);
    setAgentRun(false);
    setAgentSummary(null);
    setAgentAnswer("");

    if (!file) {
      refreshBatches();
      return;
    }

    const text = await file.text();
    const header = text.split(/\r?\n/)[0]?.split(",") || [];
    const batchIndex = header.indexOf("batch_id");
    if (batchIndex === -1) {
      setError("Uploaded CSV must include a batch_id column.");
      return;
    }
    const ids = [...new Set(
      text
        .split(/\r?\n/)
        .slice(1)
        .filter(Boolean)
        .map((line) => line.split(",")[batchIndex])
        .filter(Boolean)
    )].sort();
    setBatches(ids);
    setSelectedBatch(ids.includes("BATCH-010") ? "BATCH-010" : ids[0] || "");
  }

  async function analyzeBatch() {
    if (!selectedBatch) return;
    setLoading(true);
    setError("");
    setAgentRun(false);
    setAgentSummary(null);
    setAgentAnswer("");
    try {
      let payload;
      if (uploadedFile) {
        const form = new FormData();
        form.append("batch_id", selectedBatch);
        form.append("file", uploadedFile);
        payload = await api("/analyze", { method: "POST", body: form });
      } else {
        payload = await api(`/analyze/${selectedBatch}`);
      }
      setAnalysis(payload);
    } catch (err) {
      setError(`Analysis failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (selectedBatch) analyzeBatch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBatch, uploadedFile]);

  const risk = analysis?.risk;
  const drivers = useMemo(() => getPrimaryDrivers(analysis), [analysis]);

  async function runAgentAnalysis() {
    if (!selectedBatch) return;
    setAgentLoading(true);
    setAgentRun(true);
    setAgentAnswer("");
    try {
      let payload;
      if (uploadedFile) {
        const form = new FormData();
        form.append("batch_id", selectedBatch);
        form.append("file", uploadedFile);
        payload = await api("/agent/analyze", { method: "POST", body: form });
      } else {
        payload = await api(`/agent/analyze/${selectedBatch}`);
      }
      setAgentSummary(payload);
    } catch (err) {
      setError(`Agent analysis failed: ${err.message}`);
    } finally {
      setAgentLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark">QA</div>
          <div>
            <p className="eyebrow">Manufacturing Quality</p>
            <h1>Batch Review</h1>
          </div>
        </div>

        <SectionTitle>Connection</SectionTitle>
        <div className={`status-pill ${backendOk ? "ok" : "bad"}`}>
          <span />
          {backendOk ? "Backend connected" : "Backend offline"}
        </div>
        <a className="api-link" href={`${API_BASE_URL}/docs`} target="_blank" rel="noreferrer">
          API docs
        </a>

        <SectionTitle>Data Source</SectionTitle>
        <label className="upload-box">
          <Upload size={18} />
          <span>{uploadedFile ? uploadedFile.name : "Upload CSV"}</span>
          <input type="file" accept=".csv" onChange={handleUpload} />
        </label>
        <p className="helper-text">
          {uploadedFile ? "Using uploaded batch data" : "Using synthetic sample data"}
        </p>

        <SectionTitle>Batch Selection</SectionTitle>
        <select value={selectedBatch} onChange={(e) => setSelectedBatch(e.target.value)}>
          {batches.map((batch) => (
            <option key={batch} value={batch}>{batch}</option>
          ))}
        </select>

        <button className="primary-button" onClick={analyzeBatch} disabled={loading || !backendOk}>
          {loading ? <RotateCw className="spin" size={18} /> : <FileSearch size={18} />}
          Analyze Batch
        </button>

        <SectionTitle>View Options</SectionTitle>
        <Toggle label="Show raw data" checked={rawOpen} onChange={setRawOpen} />
        <Toggle label="Show technical details" checked={technicalOpen} onChange={setTechnicalOpen} />
      </aside>

      <main className="main-panel">
        <header className="topbar" style={{ backgroundImage: `linear-gradient(90deg, rgba(251,250,247,0.98) 0%, rgba(251,250,247,0.9) 44%, rgba(251,250,247,0.22) 100%), url(${manufacturingBg})` }}>
          <div className="topbar-copy">
            <p className="eyebrow">Agentic AI Pharma Manufacturing Deviation Intelligence System</p>
            <h2>Pharma Manufacturing Quality Assistant</h2>
            <p>Batch risk review with sensor intelligence, documentation checks, and human QA controls.</p>
          </div>
          <div className="header-meta">
            <span>{selectedBatch || "No batch selected"}</span>
            <span className="safety-chip">Decision-support only</span>
          </div>
        </header>

        {error && <div className="error-banner"><AlertTriangle size={18} />{error}</div>}

        <div className="notice-band">
          <ClipboardCheck size={18} />
          Human QA approval is required before any batch disposition.
        </div>

        <nav className="tabs">
          <button className={activeTab === "dashboard" ? "active" : ""} onClick={() => setActiveTab("dashboard")}>
            <Gauge size={18} /> Dashboard
          </button>
          <button className={activeTab === "agent" ? "active" : ""} onClick={() => setActiveTab("agent")}>
            <Bot size={18} /> AI Investigation
          </button>
        </nav>

        {!analysis ? (
          <EmptyState loading={loading} />
        ) : activeTab === "dashboard" ? (
          <Dashboard
            analysis={analysis}
            drivers={drivers}
            rawOpen={rawOpen}
            technicalOpen={technicalOpen}
          />
        ) : (
          <AgentTab
            analysis={analysis}
            drivers={drivers}
            agentRun={agentRun}
            agentLoading={agentLoading}
            agentSummary={agentSummary}
            runAgentAnalysis={runAgentAnalysis}
            agentAnswer={agentAnswer}
            setAgentAnswer={setAgentAnswer}
          />
        )}
      </main>
    </div>
  );
}

function Dashboard({ analysis, drivers, rawOpen, technicalOpen }) {
  const risk = analysis.risk;
  const batchRows = analysis.batch_rows || [];
  return (
    <>
      <section className="risk-summary">
        <div className="score-panel">
          <div className="score-heading">
            <div>
              <p className="eyebrow">Batch Risk Score</p>
              <h3>Risk position</h3>
            </div>
            <RiskBadge level={risk.risk_level} />
          </div>
          <div className="score-value-row">
            <span className="score-number">{risk.score}</span>
            <span className="score-unit">/100</span>
          </div>
          <RiskBar score={risk.score} />
        </div>
        <KpiCard label="Sensor Anomalies" value={risk.anomaly_count} detail="flagged readings" />
        <KpiCard label="Process Deviations" value={risk.deviation_count} detail="out-of-limit records" />
        <KpiCard label="Missing Docs" value={risk.missing_doc_count} detail="required fields" />
      </section>

      <section className={`recommendation ${riskClass(risk.risk_level)}`}>
        <div>
          <p className="eyebrow">QA Recommendation</p>
          <h3>{risk.risk_level}</h3>
        </div>
        <p>This tool supports review only. It cannot approve, reject, release, or disposition a batch.</p>
        <img className="pill-accent" src={pillAccent} alt="" />
      </section>

      <section className="content-grid two">
        <Panel title="Primary Risk Drivers" icon={<AlertTriangle size={18} />}>
          <ul className="driver-list">
            {drivers.map((driver) => <li key={driver}>{driver}</li>)}
          </ul>
        </Panel>
        <Panel title="Root Cause Summary" icon={<LineChart size={18} />}>
          <p className="body-copy">{analysis.root_cause_summary}</p>
        </Panel>
      </section>

      <section className="chart-grid">
        {Object.entries(SENSOR_LABELS).map(([sensor, label]) => (
          <Panel key={sensor} title={`${label} Trend`} icon={<LineChart size={18} />}>
            <SensorChart rows={batchRows} sensor={sensor} />
          </Panel>
        ))}
      </section>

      <section className="content-grid two">
        <Panel title="Process Deviations" icon={<AlertTriangle size={18} />}>
          <IssueSummary deviations={analysis.process_deviations} />
          <DataTable rows={analysis.process_deviations} />
        </Panel>
        <Panel title="Missing Documentation" icon={<ClipboardCheck size={18} />}>
          <DataTable rows={analysis.missing_documentation} />
        </Panel>
      </section>

      <section className="content-grid two">
        <Panel title="QA Review Checklist" icon={<ListChecks size={18} />}>
          <ul className="checklist">
            {analysis.qa_checklist.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </Panel>
        <Panel title="Download Report" icon={<Download size={18} />}>
          <div className="download-row">
            <DownloadButton filename={`${analysis.batch_id}_qa_report.md`} content={analysis.reports.markdown} type="text/markdown">
              Markdown Report
            </DownloadButton>
            <DownloadButton filename={`${analysis.batch_id}_qa_report.csv`} content={analysis.reports.csv} type="text/csv">
              CSV Report
            </DownloadButton>
          </div>
        </Panel>
      </section>

      {rawOpen && (
        <Panel title="Raw Analyzed Data" icon={<Database size={18} />}>
          <DataTable rows={batchRows.slice(0, 24)} />
        </Panel>
      )}

      {technicalOpen && (
        <Panel title="Technical Details" icon={<Database size={18} />}>
          <pre className="json-block">{JSON.stringify({
            backend: API_BASE_URL,
            notice: analysis.decision_support_notice,
            risk: analysis.risk,
          }, null, 2)}</pre>
        </Panel>
      )}
    </>
  );
}

function AgentTab({ analysis, drivers, agentRun, agentLoading, agentSummary, runAgentAnalysis, agentAnswer, setAgentAnswer }) {
  const steps = agentSummary?.agent_steps || [];

  function ask(question) {
    const answerMap = {
      "Which deviation should QA review first?": `QA should start with ${drivers[0] || "the highest risk finding"}, then confirm documentation completeness and quality result status.`,
      "Which timestamps are most concerning?": "Review the process deviations table for exact timestamps. Prioritize high-severity out-of-limit values and any anomaly-marked readings.",
      "What documentation must be completed?": analysis.missing_documentation?.length
        ? `Complete or verify: ${analysis.missing_documentation.map((row) => row.field.replaceAll("_", " ")).join(", ")}.`
        : "No required documentation fields are currently flagged as missing.",
    };
    setAgentAnswer(answerMap[question]);
  }

  return (
    <section className="agent-layout">
      <Panel title={`Investigation Timeline — ${analysis.batch_id}`} icon={<Bot size={18} />}>
        <p className="body-copy">
          The backend exposes the agent-style investigation flow as a sequence of specialized review agents.
          Each agent reads the same validated pipeline output and prepares QA-facing findings.
        </p>
        <button className="primary-button inline" onClick={runAgentAnalysis} disabled={agentLoading}>
          {agentLoading ? <RotateCw className="spin" size={18} /> : <Bot size={18} />}
          Run Agent Analysis
        </button>
        {agentRun && (
          <div className="timeline">
            {agentLoading && <p className="body-copy">Running agent workflow...</p>}
            {!agentLoading && steps.map((step, index) => (
              <div className="timeline-step" key={step.agent}>
                <CheckCircle2 size={18} />
                <div>
                  <strong>{index + 1}. {step.agent}</strong>
                  <p>{step.finding}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel title="Agent Finding" icon={<FileSearch size={18} />}>
        <RiskBadge level={analysis.risk.risk_level} />
        <p className="body-copy">{agentSummary?.agent_summary || analysis.root_cause_summary}</p>
        <ul className="driver-list compact">
          {drivers.map((driver) => <li key={driver}>{driver}</li>)}
        </ul>
      </Panel>

      <Panel title="Ask Follow-Up" icon={<Bot size={18} />}>
        <div className="prompt-row">
          {(agentSummary?.recommended_questions || ["Which deviation should QA review first?", "Which timestamps are most concerning?", "What documentation must be completed?"]).map((question) => (
            <button key={question} className="prompt-chip" onClick={() => ask(question)}>{question}</button>
          ))}
        </div>
        {agentAnswer && <div className="agent-answer">{agentAnswer}</div>}
      </Panel>
    </section>
  );
}

function SensorChart({ rows, sensor }) {
  const values = rows.map((row) => Number(row[sensor])).filter((value) => Number.isFinite(value));
  if (!values.length) return <p className="empty-copy">No chart data available.</p>;

  const [lower, upper] = SENSOR_LIMITS[sensor] || [Math.min(...values), Math.max(...values)];
  const min = Math.min(...values, lower);
  const max = Math.max(...values, upper);
  const width = 640;
  const height = 220;
  const pad = 28;
  const innerW = width - pad * 2;
  const innerH = height - pad * 2;
  const yScale = (value) => pad + (max - value) / (max - min || 1) * innerH;
  const xScale = (index) => pad + (index / Math.max(rows.length - 1, 1)) * innerW;
  const points = rows.map((row, index) => `${xScale(index)},${yScale(Number(row[sensor]))}`).join(" ");

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} role="img">
        <line className="grid-line" x1={pad} x2={width - pad} y1={yScale(upper)} y2={yScale(upper)} />
        <line className="grid-line" x1={pad} x2={width - pad} y1={yScale(lower)} y2={yScale(lower)} />
        <text className="limit-label" x={pad} y={yScale(upper) - 6}>Upper {upper}</text>
        <text className="limit-label" x={pad} y={yScale(lower) + 16}>Lower {lower}</text>
        <polyline className="sensor-line" points={points} />
        {rows.map((row, index) => {
          const value = Number(row[sensor]);
          const outOfLimit = value < lower || value > upper;
          return (
            <circle
              key={`${sensor}-${row.timestamp}-${index}`}
              className={row.is_anomaly ? "point anomaly" : outOfLimit ? "point deviation" : "point"}
              cx={xScale(index)}
              cy={yScale(value)}
              r={row.is_anomaly || outOfLimit ? 5 : 3}
            />
          );
        })}
      </svg>
      <div className="chart-legend">
        <span><i className="dot normal" /> Normal</span>
        <span><i className="dot deviation" /> Outside limit</span>
        <span><i className="dot anomaly" /> Model anomaly</span>
      </div>
    </div>
  );
}

function RiskBar({ score }) {
  return (
    <div className="risk-bar">
      <div className="risk-bar-track">
        <span className="risk-green" />
        <span className="risk-amber" />
        <span className="risk-red" />
        <b style={{ left: `${Math.min(Math.max(score, 0), 100)}%` }} />
      </div>
      <div className="risk-scale"><span>0</span><span>30</span><span>65</span><span>100</span></div>
    </div>
  );
}

function KpiCard({ label, value, detail }) {
  return (
    <article className="kpi-card">
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}

function Panel({ title, icon, children }) {
  return (
    <section className="panel">
      <div className="panel-title">{icon}<h3>{title}</h3></div>
      {children}
    </section>
  );
}

function DataTable({ rows }) {
  if (!rows?.length) return <p className="empty-copy">No records found.</p>;
  const columns = Object.keys(rows[0]).slice(0, 8);
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => <td key={column}>{String(row[column] ?? "")}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function IssueSummary({ deviations }) {
  if (!deviations?.length) return <p className="body-copy">No process-limit deviations detected.</p>;
  const counts = deviations.reduce((acc, row) => {
    acc[row.field] = (acc[row.field] || 0) + 1;
    return acc;
  }, {});
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  const worst = deviations.find((row) => row.severity === "High") || deviations[0];
  return (
    <div className="issue-summary">
      <span>{deviations.length} deviations</span>
      <span>Most affected: {top?.[0]?.replaceAll("_", " ")}</span>
      <span>Review: {worst?.field?.replaceAll("_", " ")} at {worst?.timestamp}</span>
    </div>
  );
}

function DownloadButton({ filename, content, type, children }) {
  function download() {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }
  return <button className="secondary-button" onClick={download}><Download size={16} />{children}</button>;
}

function RiskBadge({ level }) {
  return <span className={`risk-badge ${riskClass(level)}`}>{level}</span>;
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="toggle-row">
      <span>{label}</span>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
    </label>
  );
}

function SectionTitle({ children }) {
  return <p className="section-title">{children}</p>;
}

function EmptyState({ loading }) {
  return (
    <div className="empty-state">
      {loading ? <RotateCw className="spin" size={26} /> : <Database size={26} />}
      <p>{loading ? "Analyzing batch..." : "Choose a batch and run analysis."}</p>
    </div>
  );
}

function getPrimaryDrivers(analysis) {
  if (!analysis) return [];
  const drivers = [];
  const deviations = analysis.process_deviations || [];
  if (deviations.length) {
    const counts = deviations.reduce((acc, row) => {
      acc[row.field] = (acc[row.field] || 0) + 1;
      return acc;
    }, {});
    const [field, count] = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    drivers.push(`${field.replaceAll("_", " ")} outside limits in ${count} reading(s)`);
  }
  if (analysis.missing_documentation?.length) {
    drivers.push(`Missing documentation: ${analysis.missing_documentation.map((row) => row.field.replaceAll("_", " ")).join(", ")}`);
  }
  if (analysis.risk?.quality_failure) {
    drivers.push("Quality result is marked Fail");
  }
  if (analysis.risk?.anomaly_count) {
    drivers.push(`${analysis.risk.anomaly_count} sensor reading(s) flagged by anomaly detection`);
  }
  return drivers.length ? drivers : ["No major risk driver detected; continue standard QA review"];
}

function riskClass(level) {
  if (level?.startsWith("Low")) return "low";
  if (level?.startsWith("Medium")) return "medium";
  return "high";
}

createRoot(document.getElementById("root")).render(<App />);
