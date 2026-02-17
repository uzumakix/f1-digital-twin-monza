"""
Signal processing: time-to-distance domain resampling.

Transforms two telemetry streams from time-indexed arrays into
spatially-aligned arrays on a shared metre-resolution grid.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

logger = logging.getLogger(__name__)


@dataclass
class ResampledData:
    """Container for distance-domain resampled telemetry."""

    d: np.ndarray       # Distance grid [m]
    t_a: np.ndarray     # Elapsed time, driver A [s]
    t_b: np.ndarray     # Elapsed time, driver B [s]
    v_a: np.ndarray     # Speed, driver A [km/h]
    v_b: np.ndarray     # Speed, driver B [km/h]
    delta: np.ndarray   # Time delta: t_a - t_b [s]

    def to_dict(self) -> Dict[str, np.ndarray]:
        return {
            "d": self.d, "t_A": self.t_a, "t_B": self.t_b,
            "v_A": self.v_a, "v_B": self.v_b, "delta": self.delta,
        }


def build_interpolator(
    tel: pd.DataFrame,
    value_col: str,
    distance_col: str = "Distance",
) -> interp1d:
    """Build a piecewise-linear interpolator mapping distance to a telemetry channel.

    Deduplicates distance values to enforce monotonicity. FastF1 occasionally
    emits repeated distance readings at near-zero speed.

    Args:
        tel: Telemetry dataframe.
        value_col: Column name for the dependent variable.
        distance_col: Column name for distance (independent variable).

    Returns:
        A callable interpolator: distance -> value.
    """
    d_raw = tel[distance_col].values
    v_raw = tel[value_col].values

    _, unique_idx = np.unique(d_raw, return_index=True)
    d_clean = d_raw[unique_idx]
    v_clean = v_raw[unique_idx]

    return interp1d(
        d_clean,
        v_clean,
        kind="linear",
        bounds_error=False,
        fill_value=(v_clean[0], v_clean[-1]),
    )


def _elapsed_seconds(tel: pd.DataFrame) -> np.ndarray:
    """Compute elapsed lap time in seconds from the first telemetry sample."""
    return (tel["Time"] - tel["Time"].iloc[0]).dt.total_seconds().values


def resample_to_distance_domain(
    tel_a: pd.DataFrame,
    tel_b: pd.DataFrame,
    step: float = 1,
) -> ResampledData:
    """Resample two telemetry streams onto a common distance grid.

    Args:
        tel_a: Telemetry for driver A (reference).
        tel_b: Telemetry for driver B (comparison).
        step: Grid resolution in metres.

    Returns:
        ResampledData with aligned arrays. delta = t_a - t_b
        (negative means A is faster at that point).
    """
    logger.info("Resampling telemetry to distance domain (step=%dm)", step)

    tel_a = tel_a.copy()
    tel_b = tel_b.copy()
    tel_a["ElapsedTime"] = _elapsed_seconds(tel_a)
    tel_b["ElapsedTime"] = _elapsed_seconds(tel_b)

    d_max = min(tel_a["Distance"].max(), tel_b["Distance"].max())
    grid = np.arange(0, d_max, step)

    f_t_a = build_interpolator(tel_a, "ElapsedTime")
    f_t_b = build_interpolator(tel_b, "ElapsedTime")
    f_v_a = build_interpolator(tel_a, "Speed")
    f_v_b = build_interpolator(tel_b, "Speed")

    t_a = f_t_a(grid)
    t_b = f_t_b(grid)
    v_a = f_v_a(grid)
    v_b = f_v_b(grid)
    delta = t_a - t_b

    logger.info(
        "Grid: %d points | dt range: [%.3fs, %.3fs]",
        len(grid), delta.min(), delta.max(),
    )

    return ResampledData(d=grid, t_a=t_a, t_b=t_b, v_a=v_a, v_b=v_b, delta=delta)
