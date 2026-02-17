"""
Data export: CSV and JSON outputs for external analysis.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import Config
from src.resample import ResampledData

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")


def _ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _build_filename(cfg: Config, ext: str) -> Path:
    year = cfg.session.year
    circuit = cfg.session.circuit.lower()
    ref = cfg.drivers.reference
    comp = cfg.drivers.comparison
    return OUTPUT_DIR / f"{year}_{circuit}_{ref}_vs_{comp}.{ext}"


def export_csv(data: ResampledData, cfg: Config) -> Path:
    """Export resampled telemetry to CSV.

    Args:
        data: Resampled telemetry.
        cfg: Configuration (used for filenames and driver labels).

    Returns:
        Path to the written CSV file.
    """
    _ensure_output_dir()
    path = _build_filename(cfg, "csv")
    ref, comp = cfg.drivers.reference, cfg.drivers.comparison

    df = pd.DataFrame({
        "distance_m": data.d,
        f"speed_{ref}_kmh": data.v_a,
        f"speed_{comp}_kmh": data.v_b,
        f"elapsed_{ref}_s": data.t_a,
        f"elapsed_{comp}_s": data.t_b,
        "delta_s": data.delta,
    })
    df.to_csv(path, index=False, float_format="%.4f")
    logger.info("CSV exported: %s", path)
    return path


def export_json(data: ResampledData, cfg: Config) -> Path:
    """Export resampled telemetry to JSON with metadata.

    Args:
        data: Resampled telemetry.
        cfg: Configuration.

    Returns:
        Path to the written JSON file.
    """
    _ensure_output_dir()
    path = _build_filename(cfg, "json")
    ref, comp = cfg.drivers.reference, cfg.drivers.comparison

    payload = {
        "metadata": {
            "session": {
                "year": cfg.session.year,
                "circuit": cfg.session.circuit,
                "type": cfg.session.type,
            },
            "drivers": {"reference": ref, "comparison": comp},
            "grid_step_m": cfg.grid.step_metres,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_points": len(data.d),
            "delta_range_s": {
                "min": round(float(np.min(data.delta)), 4),
                "max": round(float(np.max(data.delta)), 4),
            },
            "final_gap_s": round(float(data.delta[-1]), 4),
        },
        "telemetry": {
            "distance_m": data.d.tolist(),
            f"speed_{ref}_kmh": data.v_a.tolist(),
            f"speed_{comp}_kmh": data.v_b.tolist(),
            f"elapsed_{ref}_s": data.t_a.tolist(),
            f"elapsed_{comp}_s": data.t_b.tolist(),
            "delta_s": data.delta.tolist(),
        },
    }

    with open(path, "w") as f:
        json.dump(payload, f, indent=2)

    logger.info("JSON exported: %s", path)
    return path
