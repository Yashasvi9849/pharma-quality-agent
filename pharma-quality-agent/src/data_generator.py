from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SENSOR_COLUMNS = [
    "temperature",
    "humidity",
    "pressure",
    "vibration",
    "compression_force",
    "ph",
]

DOCUMENTATION_COLUMNS = [
    "operator_log",
    "supervisor_review",
    "cleaning_verification",
    "deviation_reason",
]


def _batch_quality_result(batch_id: str) -> str:
    return "Fail" if batch_id in {"BATCH-004", "BATCH-007", "BATCH-010"} else "Pass"


def generate_synthetic_batches(
    num_batches: int = 12,
    rows_per_batch: int = 24,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2026-01-01 08:00:00")
    rows: list[dict[str, object]] = []

    for batch_num in range(1, num_batches + 1):
        batch_id = f"BATCH-{batch_num:03d}"
        machine_id = f"M-{(batch_num % 4) + 1:02d}"
        quality_result = _batch_quality_result(batch_id)

        base_temperature = rng.normal(22.4, 0.35, rows_per_batch)
        base_humidity = rng.normal(40.0, 2.2, rows_per_batch)
        base_pressure = rng.normal(1.22, 0.07, rows_per_batch)
        base_vibration = np.clip(rng.normal(0.32, 0.08, rows_per_batch), 0, None)
        base_compression = rng.normal(9.0, 0.25, rows_per_batch)
        base_ph = rng.normal(7.0, 0.12, rows_per_batch)

        if batch_id in {"BATCH-003", "BATCH-007"}:
            base_humidity += np.linspace(0, 14, rows_per_batch)
        if batch_id in {"BATCH-004", "BATCH-009"}:
            spike_positions = rng.choice(rows_per_batch, size=4, replace=False)
            base_vibration[spike_positions] += rng.uniform(0.55, 0.85, size=4)
        if batch_id in {"BATCH-006", "BATCH-010"}:
            base_compression -= np.linspace(0, 1.8, rows_per_batch)
        if batch_id == "BATCH-008":
            base_pressure[10:15] += 0.42
            base_temperature[16:20] += 3.0

        for step in range(rows_per_batch):
            timestamp = start + pd.Timedelta(days=batch_num - 1, minutes=step * 30)
            operator_log = "Complete"
            supervisor_review = "Reviewed"
            cleaning_verification = "Verified"
            deviation_reason = "Not applicable"

            if batch_id in {"BATCH-004", "BATCH-007"}:
                supervisor_review = ""
            if batch_id in {"BATCH-006", "BATCH-010"}:
                cleaning_verification = ""
            if batch_id in {"BATCH-003", "BATCH-008"}:
                deviation_reason = ""
            if batch_id == "BATCH-009" and step % 3 == 0:
                operator_log = ""

            rows.append(
                {
                    "batch_id": batch_id,
                    "machine_id": machine_id,
                    "timestamp": timestamp,
                    "temperature": round(float(base_temperature[step]), 2),
                    "humidity": round(float(base_humidity[step]), 2),
                    "pressure": round(float(base_pressure[step]), 3),
                    "vibration": round(float(base_vibration[step]), 3),
                    "compression_force": round(float(base_compression[step]), 2),
                    "ph": round(float(base_ph[step]), 2),
                    "operator_log": operator_log,
                    "supervisor_review": supervisor_review,
                    "cleaning_verification": cleaning_verification,
                    "deviation_reason": deviation_reason,
                    "maintenance_history": (
                        "Recent vibration calibration"
                        if batch_id in {"BATCH-004", "BATCH-009"}
                        else "Routine maintenance current"
                    ),
                    "quality_result": quality_result,
                }
            )

    return pd.DataFrame(rows)


def generate_batch_records(sensor_data: pd.DataFrame) -> pd.DataFrame:
    records = []
    for batch_id, batch_df in sensor_data.groupby("batch_id", sort=True):
        records.append(
            {
                "batch_id": batch_id,
                "machine_id": batch_df["machine_id"].iloc[0],
                "start_time": batch_df["timestamp"].min(),
                "end_time": batch_df["timestamp"].max(),
                "operator_log": _first_non_null(batch_df["operator_log"]),
                "supervisor_review": _first_non_null(batch_df["supervisor_review"]),
                "cleaning_verification": _first_non_null(batch_df["cleaning_verification"]),
                "deviation_reason": _first_non_null(batch_df["deviation_reason"]),
                "maintenance_history": _first_non_null(batch_df["maintenance_history"]),
                "quality_result": _first_non_null(batch_df["quality_result"]),
            }
        )
    return pd.DataFrame(records)


def _first_non_null(series: pd.Series) -> object:
    clean = series.dropna()
    if clean.empty:
        return ""
    return clean.iloc[0]


def ensure_sample_data(data_dir: str | Path) -> tuple[Path, Path]:
    output_dir = Path(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    batches_path = output_dir / "sample_batches.csv"
    records_path = output_dir / "sample_batch_records.csv"

    data = generate_synthetic_batches()
    records = generate_batch_records(data)
    data.to_csv(batches_path, index=False)
    records.to_csv(records_path, index=False)
    return batches_path, records_path


if __name__ == "__main__":
    ensure_sample_data(Path(__file__).resolve().parents[1] / "data")
