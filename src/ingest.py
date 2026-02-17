"""
Data ingestion: session loading and lap extraction via FastF1.
"""

from __future__ import annotations

import logging
import os
from typing import Tuple

import fastf1
import pandas as pd

logger = logging.getLogger(__name__)


def load_session(
    year: int,
    circuit: str,
    session_type: str,
    cache_dir: str = ".f1_cache",
) -> fastf1.core.Session:
    """Load a qualifying session with local disk cache.

    Args:
        year: Season year.
        circuit: Circuit name as recognised by FastF1.
        session_type: Session identifier (Q, R, FP1, etc).
        cache_dir: Path for FastF1 disk cache.

    Returns:
        Loaded session object with telemetry data.
    """
    os.makedirs(cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)

    logger.info("Loading %d %s %s", year, circuit, session_type)
    session = fastf1.get_session(year, circuit, session_type)
    session.load(telemetry=True, weather=False, messages=False)
    logger.info("Session loaded")
    return session


def extract_fastest_lap(
    session: fastf1.core.Session,
    driver: str,
) -> Tuple[pd.Series, pd.DataFrame]:
    """Extract the fastest lap and its telemetry for a driver.

    Args:
        session: A loaded FastF1 session.
        driver: Three-letter driver abbreviation (e.g. VER, SAI).

    Returns:
        Tuple of (lap Series, telemetry DataFrame with Distance column).

    Raises:
        ValueError: If no laps found for the specified driver.
    """
    laps = session.laps.pick_driver(driver)
    if laps.empty:
        raise ValueError(f"No laps found for driver {driver}")

    lap = laps.pick_fastest()
    tel = lap.get_telemetry().add_distance()
    logger.info("%s fastest: %s", driver, lap["LapTime"])
    return lap, tel
