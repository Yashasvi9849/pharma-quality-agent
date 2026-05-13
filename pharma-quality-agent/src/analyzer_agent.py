from __future__ import annotations

import json
from typing import Generator

import anthropic

from src.data_generator import SENSOR_COLUMNS


MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """You are a Pharma Manufacturing QA Analysis Agent specializing in batch quality risk assessment.

When asked to analyze a batch, you MUST call all five investigation tools in this exact sequence:
1. get_batch_data — retrieves batch records and sensor statistics
2. detect_sensor_anomalies — identifies sensor readings flagged by anomaly detection
3. check_process_deviations — checks sensor values against process specification limits
4. check_documentation_gaps — verifies required documentation fields
5. calculate_risk_score — computes the weighted risk score (anomalies 35%, deviations 35%, docs 20%, quality failure 10%)

After all five tools return results, produce a structured QA narrative that covers:
- Executive summary (risk level and top findings in 2-3 sentences)
- Sensor anomaly analysis (count, rate, which sensors were affected)
- Process deviation analysis (parameters out of spec, severity)
- Documentation completeness assessment
- Root cause hypotheses with supporting evidence
- Specific recommended QA actions prioritized by risk

IMPORTANT — DECISION SUPPORT ONLY: This system assists QA reviewers but cannot approve or reject batches.
Human QA personnel must make all final disposition decisions in accordance with SOPs."""

TOOLS = [
    {
        "name": "get_batch_data",
        "description": (
            "Retrieves a summary of batch sensor data including total record count "
            "and per-sensor statistics (mean, min, max, std deviation)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "The batch identifier to retrieve."}
            },
            "required": ["batch_id"],
        },
    },
    {
        "name": "detect_sensor_anomalies",
        "description": (
            "Runs IsolationForest anomaly detection on sensor readings. "
            "Returns anomaly count, anomaly rate percentage, and sample anomalous records."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "The batch to analyze for sensor anomalies."}
            },
            "required": ["batch_id"],
        },
    },
    {
        "name": "check_process_deviations",
        "description": (
            "Checks sensor readings against process specification limits "
            "(temperature, humidity, pressure, vibration, compression_force, pH). "
            "Returns deviations per parameter with severity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "The batch to check for process deviations."}
            },
            "required": ["batch_id"],
        },
    },
    {
        "name": "check_documentation_gaps",
        "description": (
            "Verifies required documentation fields: operator_log, supervisor_review, "
            "cleaning_verification, deviation_reason. "
            "Returns missing or incomplete fields."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "The batch to check for documentation completeness."}
            },
            "required": ["batch_id"],
        },
    },
    {
        "name": "calculate_risk_score",
        "description": (
            "Calculates the weighted risk score: anomalies 35%, deviations 35%, "
            "missing docs 20%, quality failure 10%. "
            "Returns score (0–100) and risk level (Low / Medium / High)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "The batch for which to calculate the risk score."}
            },
            "required": ["batch_id"],
        },
    },
]

TOOL_LABELS = {
    "get_batch_data": "📋 Retrieving batch data",
    "detect_sensor_anomalies": "🔬 Detecting sensor anomalies",
    "check_process_deviations": "⚠️ Checking process deviations",
    "check_documentation_gaps": "📄 Checking documentation gaps",
    "calculate_risk_score": "🎯 Calculating risk score",
}


class PharmaAnalyzerAgent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic()
        self._analysis_cache: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_analysis(self, batch_id: str, df) -> dict:
        """Runs the pipeline once and caches the result."""
        if batch_id not in self._analysis_cache:
            from src.pipeline import analyze_batch
            self._analysis_cache[batch_id] = analyze_batch(df, batch_id)
        return self._analysis_cache[batch_id]

    def _execute_tool(self, tool_name: str, tool_input: dict, df) -> str:
        batch_id = tool_input["batch_id"]
        analysis = self._get_analysis(batch_id, df)
        dispatch = {
            "get_batch_data": self._tool_get_batch_data,
            "detect_sensor_anomalies": self._tool_detect_anomalies,
            "check_process_deviations": self._tool_check_deviations,
            "check_documentation_gaps": self._tool_check_docs,
            "calculate_risk_score": self._tool_risk_score,
        }
        fn = dispatch.get(tool_name)
        if fn is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        return fn(batch_id, analysis)

    # ------------------------------------------------------------------
    # Tool implementations — each returns a JSON string
    # ------------------------------------------------------------------

    def _tool_get_batch_data(self, batch_id: str, analysis: dict) -> str:
        batch_df = analysis["dataframes"]["batch"]
        sensor_cols = [c for c in SENSOR_COLUMNS if c in batch_df.columns]
        stats: dict = {}
        for col in sensor_cols:
            s = batch_df[col].describe()
            stats[col] = {
                "mean": round(float(s["mean"]), 3),
                "min": round(float(s["min"]), 3),
                "max": round(float(s["max"]), 3),
                "std": round(float(s["std"]), 3),
            }
        return json.dumps(
            {
                "batch_id": batch_id,
                "total_records": len(batch_df),
                "sensor_columns": sensor_cols,
                "sensor_statistics": stats,
            },
            default=str,
        )

    def _tool_detect_anomalies(self, batch_id: str, analysis: dict) -> str:
        batch_df = analysis["dataframes"]["batch"]
        sensor_cols = [c for c in SENSOR_COLUMNS if c in batch_df.columns]
        anomalies = batch_df[batch_df["is_anomaly"]]
        sample_cols = [c for c in ["timestamp"] + sensor_cols + ["anomaly_score"] if c in batch_df.columns]
        return json.dumps(
            {
                "batch_id": batch_id,
                "total_records": len(batch_df),
                "anomaly_count": int(batch_df["is_anomaly"].sum()),
                "anomaly_rate_pct": round(100 * float(batch_df["is_anomaly"].mean()), 2),
                "sample_anomalous_records": anomalies[sample_cols].head(5).to_dict(orient="records"),
            },
            default=str,
        )

    def _tool_check_deviations(self, batch_id: str, analysis: dict) -> str:
        deviations = analysis["process_deviations"]
        dev_df = analysis["dataframes"]["deviations"]
        per_param: dict = {}
        if not dev_df.empty and "field" in dev_df.columns:
            per_param = {str(k): int(v) for k, v in dev_df.groupby("field").size().items()}
        return json.dumps(
            {
                "batch_id": batch_id,
                "total_deviations": len(deviations),
                "per_parameter": per_param,
                "sample_deviations": deviations[:5],
            },
            default=str,
        )

    def _tool_check_docs(self, batch_id: str, analysis: dict) -> str:
        missing_docs = analysis["missing_documentation"]
        missing_df = analysis["dataframes"]["missing_docs"]
        missing_fields: list = []
        if not missing_df.empty and "field" in missing_df.columns:
            missing_fields = missing_df["field"].tolist()
        return json.dumps(
            {
                "batch_id": batch_id,
                "total_missing": len(missing_docs),
                "missing_fields": missing_fields,
                "documentation_complete": len(missing_docs) == 0,
            },
            default=str,
        )

    def _tool_risk_score(self, batch_id: str, analysis: dict) -> str:
        risk = analysis["risk"]
        return json.dumps(
            {
                "batch_id": batch_id,
                "risk_score": risk["score"],
                "risk_level": risk["risk_level"],
                "anomaly_count": risk["anomaly_count"],
                "deviation_count": risk["deviation_count"],
                "missing_doc_count": risk["missing_doc_count"],
                "quality_failure": risk["quality_failure"],
            },
            default=str,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def analyze_batch(
        self,
        batch_id: str,
        df,
        on_tool_step=None,
    ) -> Generator[str, None, None]:
        """
        Fixed-sequence agentic loop.

        Yields text chunks for the streaming QA synthesis.
        on_tool_step(label: str, result: dict) is called after each tool executes.
        Intermediate tool-use rounds produce no text, so text only streams during
        the final synthesis turn.
        """
        messages: list[dict] = [
            {
                "role": "user",
                "content": (
                    f"Analyze batch {batch_id} for quality and safety. "
                    "Run all five investigation tools in sequence, then produce "
                    "a comprehensive QA narrative."
                ),
            }
        ]

        while True:
            with self.client.messages.stream(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text
                final_msg = stream.get_final_message()

            messages.append({"role": "assistant", "content": final_msg.content})

            if final_msg.stop_reason == "end_turn":
                break

            if final_msg.stop_reason == "tool_use":
                tool_results = []
                for block in final_msg.content:
                    if block.type == "tool_use":
                        label = TOOL_LABELS.get(block.name, block.name)
                        result_str = self._execute_tool(block.name, block.input, df)
                        if on_tool_step is not None:
                            on_tool_step(label, json.loads(result_str))
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_str,
                            }
                        )
                messages.append({"role": "user", "content": tool_results})

    def chat(
        self,
        batch_id: str,
        user_message: str,
        conversation_history: list[dict],
        df,
    ) -> Generator[str, None, None]:
        """
        Streaming chat for follow-up questions about a completed batch analysis.
        conversation_history should contain alternating user/assistant messages
        (without the initial analysis exchange).
        """
        # Prepend a brief analysis context so Claude answers in context
        context_prefix = ""
        if batch_id in self._analysis_cache:
            risk = self._analysis_cache[batch_id]["risk"]
            context_prefix = (
                f"[Batch {batch_id} analysis context — "
                f"Risk Score: {risk['score']}, Level: {risk['risk_level']}, "
                f"Anomalies: {risk['anomaly_count']}, "
                f"Deviations: {risk['deviation_count']}, "
                f"Missing Docs: {risk['missing_doc_count']}]\n\n"
            )

        messages = [
            *conversation_history,
            {"role": "user", "content": context_prefix + user_message},
        ]

        with self.client.messages.stream(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            yield from stream.text_stream
