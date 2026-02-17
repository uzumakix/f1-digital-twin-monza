"""
f1-digital-twin-monza
Entry point for the differential telemetry analysis pipeline.
"""

import argparse
import logging
import sys

from src.config import load_config
from src.ingest import load_session, extract_fastest_lap
from src.resample import resample_to_distance_domain
from src.visualise import render_chart
from src.export import export_csv, export_json

logger = logging.getLogger("f1twin")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Suppress noisy third-party loggers
    logging.getLogger("fastf1").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="f1-digital-twin",
        description="Spatial telemetry reconstruction for F1 qualifying sessions.",
    )
    parser.add_argument(
        "--config", default="configs/monza_2023.yaml",
        help="Path to session configuration file (default: configs/monza_2023.yaml)",
    )
    parser.add_argument(
        "--export", choices=["csv", "json", "both"], default=None,
        help="Export resampled data in the specified format.",
    )
    parser.add_argument(
        "--no-chart", action="store_true",
        help="Skip chart rendering (useful for data export only).",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _setup_logging(args.verbose)
    cfg = load_config(args.config)

    # 1. Load session
    session = load_session(
        cfg.session.year,
        cfg.session.circuit,
        cfg.session.type,
        cache_dir=cfg.cache_dir,
    )

    # 2. Extract fastest laps
    lap_a, tel_a = extract_fastest_lap(session, cfg.drivers.reference)
    lap_b, tel_b = extract_fastest_lap(session, cfg.drivers.comparison)

    # 3. Resample to distance domain
    data = resample_to_distance_domain(tel_a, tel_b, step=cfg.grid.step_metres)

    # 4. Render chart
    if not args.no_chart:
        render_chart(data, cfg)

    # 5. Export data
    if args.export in ("csv", "both"):
        export_csv(data, cfg)
    if args.export in ("json", "both"):
        export_json(data, cfg)

    logger.info("Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
