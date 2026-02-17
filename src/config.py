"""
Typed configuration with dataclass validation and YAML loading.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SessionConfig:
    year: int = 2023
    circuit: str = "Monza"
    type: str = "Q"


@dataclass
class DriverConfig:
    reference: str = "VER"
    comparison: str = "SAI"


@dataclass
class GridConfig:
    step_metres: int = 1


@dataclass
class OutputConfig:
    filename: str = "telemetry_analysis.png"
    dpi: int = 200


@dataclass
class ThemeConfig:
    bg_dark: str = "#0e1117"
    bg_panel: str = "#161b22"
    grid_color: str = "#30363d"
    text_color: str = "#e6edf3"
    text_secondary: str = "#94a3b8"
    text_muted: str = "#64748b"
    speed_a: str = "#3b82f6"
    speed_b: str = "#e8002d"
    fill_a: str = "#3b82f6"
    fill_b: str = "#22c55e"
    zero_line: str = "#94a3b8"


@dataclass
class Config:
    session: SessionConfig = field(default_factory=SessionConfig)
    drivers: DriverConfig = field(default_factory=DriverConfig)
    grid: GridConfig = field(default_factory=GridConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    corners: List[Tuple[str, int]] = field(default_factory=lambda: [
        ("T1 Grande", 295),
        ("T2 Grande", 370),
        ("Roggia", 680),
        ("Roggia", 750),
        ("Lesmo 1", 1430),
        ("Lesmo 2", 1650),
        ("Ascari", 3450),
        ("Ascari", 3560),
        ("Ascari", 3640),
        ("Parabolica", 4400),
    ])
    cache_dir: str = ".f1_cache"


def load_config(path: str) -> Config:
    """Load YAML configuration file and return a validated Config object."""
    cfg = Config()

    if not os.path.exists(path):
        logger.warning("Config not found at %s, using defaults", path)
        return cfg

    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}

    if "session" in raw:
        cfg.session = SessionConfig(**raw["session"])
    if "drivers" in raw:
        cfg.drivers = DriverConfig(**raw["drivers"])
    if "grid" in raw:
        cfg.grid = GridConfig(**raw["grid"])
    if "output" in raw:
        cfg.output = OutputConfig(**raw["output"])
    if "theme" in raw:
        cfg.theme = ThemeConfig(**raw["theme"])
    if "corners" in raw:
        cfg.corners = [(name, dist) for name, dist in raw["corners"]]
    if "cache_dir" in raw:
        cfg.cache_dir = raw["cache_dir"]

    return cfg
