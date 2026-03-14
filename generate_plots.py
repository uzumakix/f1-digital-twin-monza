"""
generate_plots.py
Generates the static braking zone analysis chart for the README.
Uses real 2023 Monza Q telemetry via FastF1.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d
from pipeline import run_pipeline


def save_braking_chart(data, out="results/braking_analysis.png"):
    """Dual-panel chart: speed + deceleration through T1."""
    zone_a = data["zone_a"]
    zone_b = data["zone_b"]
    da, db = data["driver_a"], data["driver_b"]
    ca, cb = data["color_a"], data["color_b"]
    bp_a, bp_b = data["brake_point_a"], data["brake_point_b"]

    bg = "#0e1117"
    panel = "#1a1a2e"
    grid_c = "#2a2a4a"
    text_c = "#e0e0e0"
    muted = "#888888"

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 8), sharex=True,
        facecolor=bg, gridspec_kw={"height_ratios": [1, 1.2], "hspace": 0.08}
    )

    # speed panel
    ax1.set_facecolor(panel)
    ax1.plot(zone_a["Distance"], zone_a["Speed"], color=ca,
             linewidth=1.8, label=da, alpha=0.95)
    ax1.plot(zone_b["Distance"], zone_b["Speed"], color=cb,
             linewidth=1.8, label=db, alpha=0.85)

    if bp_a is not None:
        ax1.axvline(bp_a, color=ca, linestyle="--", linewidth=1, alpha=0.6)
        ax1.text(bp_a + 5, 120, f"{da} brake\n{bp_a:.0f}m",
                 fontsize=7, color=ca, fontfamily="monospace")
    if bp_b is not None:
        ax1.axvline(bp_b, color=cb, linestyle="--", linewidth=1, alpha=0.6)
        ax1.text(bp_b + 5, 150, f"{db} brake\n{bp_b:.0f}m",
                 fontsize=7, color=cb, fontfamily="monospace")

    ax1.set_ylabel("Speed [km/h]", fontsize=10, color=text_c)
    ax1.tick_params(colors=muted, labelsize=8)
    ax1.legend(loc="upper right", framealpha=0, fontsize=9, labelcolor=text_c)
    ax1.grid(color=grid_c, linewidth=0.3, alpha=0.5)
    for s in ax1.spines.values():
        s.set_edgecolor(grid_c)

    # deceleration panel
    ax2.set_facecolor(panel)
    smooth_a = uniform_filter1d(zone_a["Accel_G"].values, size=5)
    smooth_b = uniform_filter1d(zone_b["Accel_G"].values, size=5)

    ax2.plot(zone_a["Distance"].values, smooth_a, color=ca,
             linewidth=1.8, label=f"{da} decel", alpha=0.95)
    ax2.plot(zone_b["Distance"].values, smooth_b, color=cb,
             linewidth=1.8, label=f"{db} decel", alpha=0.85)

    ax2.axhline(0, color=muted, linewidth=0.6)
    ax2.fill_between(zone_a["Distance"].values, 0, smooth_a,
                     where=(smooth_a < 0), alpha=0.15, color=ca)
    ax2.fill_between(zone_b["Distance"].values, 0, smooth_b,
                     where=(smooth_b < 0), alpha=0.12, color=cb)

    peak_a = data["peak_decel_a"]
    peak_b = data["peak_decel_b"]
    ax2.text(0.02, 0.06,
             f"Peak: {da} {peak_a:.2f}G  |  {db} {peak_b:.2f}G",
             transform=ax2.transAxes, fontsize=8, color=text_c,
             fontfamily="monospace",
             bbox=dict(boxstyle="round,pad=0.4", fc=panel, ec=grid_c, lw=0.8))

    ax2.set_ylabel("Longitudinal Accel [G]", fontsize=10, color=text_c)
    ax2.set_xlabel("Distance [m]", fontsize=10, color=text_c)
    ax2.tick_params(colors=muted, labelsize=8)
    ax2.legend(loc="lower right", framealpha=0, fontsize=8, labelcolor=text_c)
    ax2.grid(color=grid_c, linewidth=0.3, alpha=0.5)
    for s in ax2.spines.values():
        s.set_edgecolor(grid_c)

    fig.suptitle("MONZA 2023 Q  |  TURN 1 BRAKING ZONE",
                 color=text_c, fontsize=13, fontweight="bold",
                 fontfamily="monospace", y=0.96)
    fig.text(0.5, 0.925,
             f"Speed and longitudinal deceleration (a = dv/dt)  |  {da} vs {db}",
             ha="center", color=muted, fontsize=9, fontfamily="monospace")

    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=bg)
    plt.close(fig)
    print(f"  -> {out}")


def save_full_lap_speed(data, out="results/full_lap_speed.png"):
    """Full-lap speed trace with T1 zone highlighted."""
    tel_a = data["tel_a"]
    tel_b = data["tel_b"]
    da, db = data["driver_a"], data["driver_b"]
    ca, cb = data["color_a"], data["color_b"]

    bg = "#0e1117"
    panel = "#1a1a2e"
    grid_c = "#2a2a4a"
    text_c = "#e0e0e0"
    muted = "#888888"

    fig, ax = plt.subplots(figsize=(16, 5), facecolor=bg)
    ax.set_facecolor(panel)

    ax.plot(tel_a["Distance"], tel_a["Speed"], color=ca,
            linewidth=1.0, label=da, alpha=0.9)
    ax.plot(tel_b["Distance"], tel_b["Speed"], color=cb,
            linewidth=1.0, label=db, alpha=0.8)

    # highlight T1 zone
    ax.axvspan(250, 750, alpha=0.08, color="#ffffff", label="T1 zone")
    ax.text(500, 355, "T1", ha="center", fontsize=9, color=muted,
            fontfamily="monospace")

    ax.set_ylabel("Speed [km/h]", fontsize=10, color=text_c)
    ax.set_xlabel("Distance [m]", fontsize=10, color=text_c)
    ax.set_ylim(50, 370)
    ax.tick_params(colors=muted, labelsize=8)
    ax.legend(loc="lower right", framealpha=0, fontsize=9, labelcolor=text_c)
    ax.grid(color=grid_c, linewidth=0.3, alpha=0.5)
    for s in ax.spines.values():
        s.set_edgecolor(grid_c)

    fig.suptitle(f"FULL LAP SPEED TRACE  |  MONZA 2023 Q  |  {da} vs {db}",
                 color=text_c, fontsize=11, fontweight="bold",
                 fontfamily="monospace", y=0.97)

    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=bg)
    plt.close(fig)
    print(f"  -> {out}")


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    print("Loading 2023 Monza Q telemetry...\n")
    data = run_pipeline()

    da, db = data["driver_a"], data["driver_b"]
    print(f"{da} brake point: {data['brake_point_a']:.0f} m")
    print(f"{db} brake point: {data['brake_point_b']:.0f} m")
    print(f"{da} peak decel:  {data['peak_decel_a']:.2f} G")
    print(f"{db} peak decel:  {data['peak_decel_b']:.2f} G\n")

    save_braking_chart(data)
    save_full_lap_speed(data)
    print("\ndone.")
