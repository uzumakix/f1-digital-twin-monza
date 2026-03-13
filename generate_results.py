"""
generate_results.py
Generates all figures for the repo using real 2023 Monza Q data.
Requires network on first run. Cached after that.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.ticker import MultipleLocator
from scipy.interpolate import interp1d

import fastf1

from src.config import load_config
from src.ingest import load_session, extract_fastest_lap
from src.resample import resample_to_distance_domain, build_interpolator
from src.visualise import render_chart


BG = "#0e1117"
PANEL = "#161b22"
GRID_C = "#30363d"
TXT = "#e6edf3"
TXT2 = "#94a3b8"
BLUE = "#3b82f6"
RED = "#e8002d"
GREEN = "#22c55e"


def _get_data():
    """Load session and return telemetry + resampled data."""
    cfg = load_config("configs/monza_2023.yaml")
    session = load_session(cfg.session.year, cfg.session.circuit,
                           cfg.session.type, cache_dir=cfg.cache_dir)
    laps = session.laps

    ver_lap = laps.pick_drivers("VER").pick_fastest()
    sai_lap = laps.pick_drivers("SAI").pick_fastest()

    tel_v = ver_lap.get_telemetry()
    tel_s = sai_lap.get_telemetry()

    # add distance if missing
    if "Distance" not in tel_v.columns:
        tel_v = tel_v.add_distance()
    if "Distance" not in tel_s.columns:
        tel_s = tel_s.add_distance()

    data = resample_to_distance_domain(tel_v, tel_s, step=1)
    return tel_v, tel_s, ver_lap, sai_lap, data, cfg


def fig_track_speed(tel_v, tel_s, out="results/track_speed_map.png"):
    """Track map colored by speed. Shows the actual circuit layout."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), facecolor=BG)

    for ax, tel, name, color_label in [
        (axes[0], tel_v, "VER", "Speed [km/h]"),
        (axes[1], tel_s, "SAI", "Speed [km/h]"),
    ]:
        ax.set_facecolor(BG)
        x = tel["X"].values
        y = tel["Y"].values
        speed = tel["Speed"].values

        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap="RdYlGn_r", linewidth=3.5)
        lc.set_array(speed)
        lc.set_clim(70, 350)
        ax.add_collection(lc)

        ax.set_xlim(x.min() - 500, x.max() + 500)
        ax.set_ylim(y.min() - 500, y.max() + 500)
        ax.set_aspect("equal")
        ax.set_title(name, color=TXT, fontsize=14, fontweight="bold",
                     fontfamily="monospace")
        ax.axis("off")

        cbar = fig.colorbar(lc, ax=ax, fraction=0.025, pad=0.02)
        cbar.set_label("km/h", color=TXT2, fontsize=9)
        cbar.ax.tick_params(colors=TXT2, labelsize=7)

    fig.suptitle("MONZA 2023 Q | TRACK SPEED MAP",
                 color=TXT, fontsize=12, fontweight="bold",
                 fontfamily="monospace", y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  -> {out}")


def fig_track_delta(tel_v, tel_s, data, out="results/track_delta_map.png"):
    """Track map colored by who's faster at each point."""
    fig, ax = plt.subplots(figsize=(9, 8), facecolor=BG)
    ax.set_facecolor(BG)

    # interpolate delta onto VER's x/y positions
    x = tel_v["X"].values
    y = tel_v["Y"].values
    dist_v = tel_v["Distance"].values

    # build delta interpolator from resampled data
    f_delta = interp1d(data.d, data.delta, kind="linear",
                       bounds_error=False, fill_value=0.0)
    delta_on_track = f_delta(dist_v)

    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    lc = LineCollection(segments, cmap="RdBu", linewidth=4.5)
    lc.set_array(delta_on_track[:-1])
    vmax = max(abs(delta_on_track.min()), abs(delta_on_track.max()))
    lc.set_clim(-vmax, vmax)
    ax.add_collection(lc)

    ax.set_xlim(x.min() - 500, x.max() + 500)
    ax.set_ylim(y.min() - 500, y.max() + 500)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.set_title("VER vs SAI | TIME DELTA ON TRACK",
                 color=TXT, fontsize=13, fontweight="bold",
                 fontfamily="monospace", pad=15)
    ax.text(0.5, 0.02, "blue = VER ahead  |  red = SAI ahead",
            transform=ax.transAxes, ha="center", color=TXT2, fontsize=9,
            fontfamily="monospace")

    cbar = fig.colorbar(lc, ax=ax, fraction=0.025, pad=0.02, shrink=0.8)
    cbar.set_label("dt [s]", color=TXT2, fontsize=9)
    cbar.ax.tick_params(colors=TXT2, labelsize=7)

    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  -> {out}")


def fig_inputs(tel_v, tel_s, out="results/driver_inputs.png"):
    """Throttle, brake, and gear comparison across the lap."""
    fig, axes = plt.subplots(4, 1, figsize=(16, 10), facecolor=BG,
                             sharex=True)

    dist_v = tel_v["Distance"].values
    dist_s = tel_s["Distance"].values

    panels = [
        ("Speed [km/h]", "Speed", False),
        ("Throttle [%]", "Throttle", False),
        ("Brake", "Brake", True),
        ("Gear", "nGear", False),
    ]

    for ax, (ylabel, col, is_brake) in zip(axes, panels):
        ax.set_facecolor(PANEL)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_C)
        ax.tick_params(colors=TXT2, labelsize=7)
        ax.grid(color=GRID_C, linewidth=0.3, linestyle="--", alpha=0.5)
        ax.set_axisbelow(True)
        ax.yaxis.label.set_color(TXT)

        v_data = tel_v[col].values
        s_data = tel_s[col].values

        if is_brake:
            v_data = v_data.astype(float) * 100
            s_data = s_data.astype(float) * 100

        ax.plot(dist_v, v_data, color=BLUE, linewidth=0.9, label="VER", alpha=0.9)
        ax.plot(dist_s, s_data, color=RED, linewidth=0.9, label="SAI", alpha=0.75)
        ax.set_ylabel(ylabel, fontsize=8, color=TXT, labelpad=4)

    axes[0].legend(loc="upper right", framealpha=0, fontsize=8,
                   labelcolor=TXT, handlelength=1.4)
    axes[-1].set_xlabel("Distance [m]", fontsize=9, color=TXT)
    fig.suptitle("DRIVER INPUTS | VER vs SAI | MONZA 2023 Q",
                 color=TXT, fontsize=12, fontweight="bold",
                 fontfamily="monospace", y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  -> {out}")


def fig_main_chart(data, cfg, out="results/telemetry_analysis.png"):
    """The main two-panel chart (speed + delta)."""
    cfg.output.filename = out
    render_chart(data, cfg)
    print(f"  -> {out}")


def fig_delta_detail(data, cfg, out="results/delta_detail.png"):
    """Clean delta trace, light theme."""
    d = data.d
    delta = data.delta
    ref = cfg.drivers.reference
    comp = cfg.drivers.comparison

    plt.rcParams.update({
        "figure.facecolor": "#fafafa", "axes.facecolor": "#ffffff",
        "axes.edgecolor": "#cccccc", "axes.labelcolor": "#333333",
        "axes.grid": True, "grid.color": "#e8e8e8", "grid.linewidth": 0.5,
        "text.color": "#333333", "xtick.color": "#555555",
        "ytick.color": "#555555", "font.family": "serif", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
    })

    fig, ax = plt.subplots(figsize=(13, 4))
    ax.fill_between(d, 0, delta, where=(delta >= 0), interpolate=True,
                    color=GREEN, alpha=0.3, label=f"{comp} faster")
    ax.fill_between(d, 0, delta, where=(delta < 0), interpolate=True,
                    color=BLUE, alpha=0.3, label=f"{ref} faster")
    ax.plot(d, delta, color="#333333", linewidth=0.7)
    ax.axhline(0, color="#999999", linewidth=0.5, linestyle="--")

    for name, dist in cfg.corners:
        if dist < d[-1]:
            ax.axvline(dist, color="#cccccc", linewidth=0.5, linestyle=":", alpha=0.6)
            ax.text(dist, ax.get_ylim()[0] * 0.05, f" {name}", fontsize=6.5,
                    color="#888888", va="bottom", rotation=90)

    ax.set_xlabel("distance [m]")
    ax.set_ylabel(f"dt [s]  (neg = {ref} ahead)")
    ax.set_title(f"{ref} vs {comp} | {cfg.session.year} {cfg.session.circuit} {cfg.session.type}")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out}")


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    print("Loading 2023 Monza Q telemetry...\n")
    tel_v, tel_s, ver_lap, sai_lap, data, cfg = _get_data()

    print(f"VER: {ver_lap['LapTime']} ({ver_lap['Compound']})")
    print(f"SAI: {sai_lap['LapTime']} ({sai_lap['Compound']})")
    print(f"gap: {data.delta[-1]:.3f}s\n")

    fig_main_chart(data, cfg)
    fig_delta_detail(data, cfg)
    fig_track_speed(tel_v, tel_s)
    fig_track_delta(tel_v, tel_s, data)
    fig_inputs(tel_v, tel_s)
    print("\ndone.")
