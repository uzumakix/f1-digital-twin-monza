"""
generate_results.py
Runs the real pipeline and saves output to results/.
Requires network on first run (FastF1 downloads ~50-80 MB).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import load_config
from src.ingest import load_session, extract_fastest_lap
from src.resample import resample_to_distance_domain
from src.visualise import render_chart


def generate_delta_detail(data, cfg, out="results/delta_detail.png"):
    """Zoomed-in delta trace with corner labels. Light theme for contrast."""
    d = data.d
    delta = data.delta
    ref = cfg.drivers.reference
    comp = cfg.drivers.comparison

    plt.rcParams.update({
        "figure.facecolor": "#fafafa",
        "axes.facecolor": "#ffffff",
        "axes.edgecolor": "#cccccc",
        "axes.labelcolor": "#333333",
        "axes.grid": True,
        "grid.color": "#e8e8e8",
        "grid.linewidth": 0.5,
        "text.color": "#333333",
        "xtick.color": "#555555",
        "ytick.color": "#555555",
        "font.family": "serif",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })

    fig, ax = plt.subplots(figsize=(13, 4))
    ax.fill_between(d, 0, delta, where=(delta >= 0), interpolate=True,
                    color="#22c55e", alpha=0.3, label=f"{comp} faster")
    ax.fill_between(d, 0, delta, where=(delta < 0), interpolate=True,
                    color="#3b82f6", alpha=0.3, label=f"{ref} faster")
    ax.plot(d, delta, color="#333333", linewidth=0.7)
    ax.axhline(0, color="#999999", linewidth=0.5, linestyle="--")

    for name, dist in cfg.corners:
        if dist < d[-1]:
            ax.axvline(dist, color="#cccccc", linewidth=0.5, linestyle=":", alpha=0.6)
            ax.text(dist, ax.get_ylim()[0] * 0.05, f" {name}", fontsize=6.5,
                    color="#888888", va="bottom", rotation=90)

    ax.set_xlabel("distance [m]")
    ax.set_ylabel(f"dt [s]  (neg = {ref} ahead)")
    ax.set_title(f"cumulative time delta: {ref} vs {comp}, "
                 f"{cfg.session.year} {cfg.session.circuit} {cfg.session.type}")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out}")


def main():
    os.makedirs("results", exist_ok=True)
    cfg = load_config("configs/monza_2023.yaml")

    # override output path to results/
    cfg.output.filename = "results/telemetry_analysis.png"

    print("Loading session...")
    session = load_session(cfg.session.year, cfg.session.circuit,
                           cfg.session.type, cache_dir=cfg.cache_dir)

    print("Extracting fastest laps...")
    _, tel_a = extract_fastest_lap(session, cfg.drivers.reference)
    _, tel_b = extract_fastest_lap(session, cfg.drivers.comparison)

    print("Resampling...")
    data = resample_to_distance_domain(tel_a, tel_b, step=cfg.grid.step_metres)

    print("Rendering charts...")
    render_chart(data, cfg)
    print(f"  -> {cfg.output.filename}")
    generate_delta_detail(data, cfg)

    print(f"\nfinal gap: {data.delta[-1]:.3f}s")
    print(f"grid points: {len(data.d)}")
    print("done.")


if __name__ == "__main__":
    main()
