"""
generate_results.py
All figures for the repo. Real 2023 Monza Q data via FastF1.
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy.interpolate import interp1d

import fastf1
import fastf1.plotting as fp

from src.config import load_config
from src.ingest import load_session, extract_fastest_lap
from src.resample import resample_to_distance_domain
from src.visualise import render_chart


def _rotate(x, y, angle_deg):
    """Rotate x/y coordinates by angle (degrees)."""
    a = np.radians(angle_deg)
    xr = x * np.cos(a) - y * np.sin(a)
    yr = x * np.sin(a) + y * np.cos(a)
    return xr, yr


def _get_data():
    cfg = load_config("configs/monza_2023.yaml")
    session = load_session(cfg.session.year, cfg.session.circuit,
                           cfg.session.type, cache_dir=cfg.cache_dir)

    ver_lap = session.laps.pick_drivers("VER").pick_fastest()
    sai_lap = session.laps.pick_drivers("SAI").pick_fastest()
    tel_v = ver_lap.get_telemetry()
    tel_s = sai_lap.get_telemetry()

    if "Distance" not in tel_v.columns:
        tel_v = tel_v.add_distance()
    if "Distance" not in tel_s.columns:
        tel_s = tel_s.add_distance()

    data = resample_to_distance_domain(tel_v, tel_s, step=1)
    ci = session.get_circuit_info()

    ver_color = fp.get_driver_color("VER", session)
    sai_color = fp.get_driver_color("SAI", session)

    return tel_v, tel_s, ver_lap, sai_lap, data, cfg, ci, session, ver_color, sai_color


def fig_track_delta(tel_v, data, ci, ver_color, sai_color,
                    out="results/track_delta.png"):
    """Track layout colored by time delta. Rotated properly."""
    x_raw = tel_v["X"].values.astype(float)
    y_raw = tel_v["Y"].values.astype(float)
    dist_v = tel_v["Distance"].values.astype(float)

    # rotate to match broadcast angle
    x, y = _rotate(x_raw, y_raw, ci.rotation)

    # interpolate delta onto track positions
    f_delta = interp1d(data.d, data.delta, kind="linear",
                       bounds_error=False, fill_value=0.0)
    delta_on_track = f_delta(dist_v)

    fig, ax = plt.subplots(figsize=(12, 7), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap="RdBu_r", linewidth=5.5,
                        capstyle="round", joinstyle="round")
    lc.set_array(delta_on_track[:-1])
    vmax = np.percentile(np.abs(delta_on_track), 98)
    lc.set_clim(-vmax, vmax)
    ax.add_collection(lc)

    # corner numbers
    for _, row in ci.corners.iterrows():
        cx, cy = _rotate(row["X"], row["Y"], ci.rotation)
        ax.annotate(str(int(row["Number"])), xy=(cx, cy),
                    fontsize=7, color="#aaaaaa", fontweight="bold",
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.15", fc="#1a1a2e",
                              ec="#555555", lw=0.5))

    pad = 800
    ax.set_xlim(x.min() - pad, x.max() + pad)
    ax.set_ylim(y.min() - pad, y.max() + pad)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.text(0.5, 0.97, "MONZA 2023 QUALIFYING",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=14, fontweight="bold", color="#e0e0e0",
            fontfamily="monospace")
    ax.text(0.5, 0.93, "time delta on track | VER vs SAI",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=10, color="#888888", fontfamily="monospace")

    # legend
    ax.text(0.02, 0.06, f"VER faster", transform=ax.transAxes,
            fontsize=9, color=ver_color, fontweight="bold", fontfamily="monospace")
    ax.text(0.02, 0.02, f"SAI faster", transform=ax.transAxes,
            fontsize=9, color=sai_color, fontweight="bold", fontfamily="monospace")

    cbar = fig.colorbar(lc, ax=ax, fraction=0.02, pad=0.01, shrink=0.6)
    cbar.set_label("dt [s]", color="#aaaaaa", fontsize=9)
    cbar.ax.tick_params(colors="#aaaaaa", labelsize=7)

    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig)
    print(f"  -> {out}")


def fig_speed_comparison(tel_v, tel_s, ci, ver_color, sai_color,
                         out="results/speed_comparison.png"):
    """Side-by-side track colored by speed, properly rotated."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), facecolor="#1a1a2e")

    for ax, tel, name, team_color in [
        (axes[0], tel_v, "VER  1:20.307", ver_color),
        (axes[1], tel_s, "SAI  1:20.294", sai_color),
    ]:
        ax.set_facecolor("#1a1a2e")
        x_raw = tel["X"].values.astype(float)
        y_raw = tel["Y"].values.astype(float)
        x, y = _rotate(x_raw, y_raw, ci.rotation)
        speed = tel["Speed"].values.astype(float)

        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap="plasma", linewidth=4,
                            capstyle="round")
        lc.set_array(speed)
        lc.set_clim(70, 350)
        ax.add_collection(lc)

        pad = 800
        ax.set_xlim(x.min() - pad, x.max() + pad)
        ax.set_ylim(y.min() - pad, y.max() + pad)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(name, color=team_color, fontsize=13, fontweight="bold",
                     fontfamily="monospace", pad=10)

    cbar = fig.colorbar(axes[0].collections[0], ax=axes, fraction=0.015,
                        pad=0.02, shrink=0.7)
    cbar.set_label("speed [km/h]", color="#aaaaaa", fontsize=9)
    cbar.ax.tick_params(colors="#aaaaaa", labelsize=7)

    fig.suptitle("SPEED ON TRACK", color="#e0e0e0", fontsize=12,
                 fontweight="bold", fontfamily="monospace", y=0.98)
    fig.tight_layout(rect=[0, 0, 0.95, 0.95])
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig)
    print(f"  -> {out}")


def fig_inputs(tel_v, tel_s, ver_color, sai_color,
               out="results/driver_inputs.png"):
    """Throttle, brake, gear, speed overlay."""
    bg = "#1a1a2e"
    panel = "#16213e"
    grid_c = "#2a2a4a"

    fig, axes = plt.subplots(4, 1, figsize=(16, 9), facecolor=bg, sharex=True)

    panels = [
        ("Speed [km/h]", "Speed", False),
        ("Throttle [%]", "Throttle", False),
        ("Brake", "Brake", True),
        ("Gear", "nGear", False),
    ]

    for ax, (ylabel, col, is_brake) in zip(axes, panels):
        ax.set_facecolor(panel)
        for spine in ax.spines.values():
            spine.set_edgecolor(grid_c)
        ax.tick_params(colors="#888888", labelsize=7)
        ax.grid(color=grid_c, linewidth=0.3, linestyle="-", alpha=0.4)
        ax.set_axisbelow(True)

        v_data = tel_v[col].values.astype(float)
        s_data = tel_s[col].values.astype(float)
        if is_brake:
            v_data *= 100
            s_data *= 100

        ax.plot(tel_v["Distance"].values, v_data, color=ver_color,
                linewidth=0.8, label="VER", alpha=0.9)
        ax.plot(tel_s["Distance"].values, s_data, color=sai_color,
                linewidth=0.8, label="SAI", alpha=0.8)
        ax.set_ylabel(ylabel, fontsize=8, color="#cccccc", labelpad=4)

    axes[0].legend(loc="lower right", framealpha=0, fontsize=8,
                   labelcolor="#cccccc", handlelength=1.4)
    axes[-1].set_xlabel("Distance [m]", fontsize=9, color="#cccccc")

    fig.suptitle("VER vs SAI  |  DRIVER INPUTS  |  MONZA 2023 Q",
                 color="#e0e0e0", fontsize=11, fontweight="bold",
                 fontfamily="monospace", y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor=bg)
    plt.close(fig)
    print(f"  -> {out}")


def fig_main_chart(data, cfg, out="results/telemetry_analysis.png"):
    cfg.output.filename = out
    render_chart(data, cfg)
    print(f"  -> {out}")


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    print("Loading 2023 Monza Q...\n")
    tel_v, tel_s, ver_lap, sai_lap, data, cfg, ci, session, ver_c, sai_c = _get_data()

    print(f"VER: {ver_lap['LapTime']} ({ver_lap['Compound']})")
    print(f"SAI: {sai_lap['LapTime']} ({sai_lap['Compound']})")
    print(f"gap: {data.delta[-1]:.3f}s\n")

    fig_track_delta(tel_v, data, ci, ver_c, sai_c)
    fig_speed_comparison(tel_v, tel_s, ci, ver_c, sai_c)
    fig_inputs(tel_v, tel_s, ver_c, sai_c)
    fig_main_chart(data, cfg)
    print("\ndone.")
