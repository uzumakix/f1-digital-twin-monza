"""
generate_results.py
Generates example output using synthetic telemetry that models the
Monza 2023 speed profile. Used for README screenshots.

The real pipeline uses FastF1 live data. This script generates
representative synthetic data so the repo has example output
without requiring a network connection.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# Monza corner positions (metres) and approximate minimum speeds (km/h)
# These are rough but realistic for the 2023 layout
CORNERS = [
    ("T1 Grande", 295, 85),
    ("T2 Grande", 370, 75),
    ("Roggia", 680, 80),
    ("Roggia exit", 750, 90),
    ("Lesmo 1", 1430, 195),
    ("Lesmo 2", 1650, 175),
    ("Ascari entry", 3450, 190),
    ("Ascari mid", 3560, 185),
    ("Ascari exit", 3640, 200),
    ("Parabolica", 4400, 165),
]

TRACK_LENGTH = 5793  # metres


def _build_speed_profile(corners, track_len, n_points=5000, seed=0):
    """Build a realistic speed trace using corner waypoints.

    Between corners the car accelerates toward ~345 km/h.
    At corners the speed drops to the minimum then climbs back.
    """
    rng = np.random.default_rng(seed)
    d = np.linspace(0, track_len, n_points)
    v = np.full(n_points, 340.0)  # start at top speed

    for name, pos, min_speed in corners:
        # braking zone: ~200m before corner, speed drops from current to min
        brake_start = max(pos - 200, 0)
        brake_end = pos
        # acceleration zone: from corner to ~400m after
        accel_end = min(pos + 400, track_len)

        for i in range(n_points):
            if brake_start <= d[i] <= brake_end:
                # smooth braking curve
                frac = (d[i] - brake_start) / (brake_end - brake_start)
                local_max = v[i]
                drop = (local_max - min_speed) * (frac ** 1.5)
                v[i] = max(v[i] - drop, min_speed)
            elif brake_end < d[i] <= accel_end:
                # acceleration out of corner
                frac = (d[i] - brake_end) / (accel_end - brake_end)
                v[i] = min_speed + (340 - min_speed) * (frac ** 0.7)

    # add small noise for realism
    v += rng.normal(0, 1.5, n_points)
    v = np.clip(v, 60, 350)
    return d, v


def _speed_to_time(d, v):
    """Integrate speed profile to get elapsed time at each distance point."""
    # v is in km/h, d is in metres
    v_ms = v / 3.6  # convert to m/s
    dt = np.diff(d) / v_ms[:-1]
    t = np.concatenate([[0], np.cumsum(dt)])
    return t


def _format_lap(seconds):
    m, s = divmod(seconds, 60)
    return f"{int(m)}:{s:06.3f}"


def generate_chart(out="results/telemetry_analysis.png"):
    """Generate the two-panel telemetry chart matching the tool's output style."""

    # Build two slightly different speed profiles (VER vs SAI)
    d_ver, v_ver = _build_speed_profile(CORNERS, TRACK_LENGTH, seed=42)

    # SAI: slightly different corner speeds to create realistic delta
    corners_sai = [
        ("T1 Grande", 295, 83),   # SAI brakes later, lower min
        ("T2 Grande", 370, 73),
        ("Roggia", 680, 77),      # better through chicanes
        ("Roggia exit", 750, 88),
        ("Lesmo 1", 1430, 190),   # VER is faster here
        ("Lesmo 2", 1650, 170),
        ("Ascari entry", 3450, 186),
        ("Ascari mid", 3560, 182),
        ("Ascari exit", 3640, 196),
        ("Parabolica", 4400, 162),
    ]
    d_sai, v_sai = _build_speed_profile(corners_sai, TRACK_LENGTH, seed=99)

    t_ver = _speed_to_time(d_ver, v_ver)
    t_sai = _speed_to_time(d_sai, v_sai)
    delta = t_ver - t_sai  # negative = VER ahead

    lap_ver = t_ver[-1]
    lap_sai = t_sai[-1]
    gap = lap_ver - lap_sai

    # -- chart styling (matches src/visualise.py dark theme) --
    BG_DARK = "#0e1117"
    BG_PANEL = "#161b22"
    GRID_C = "#30363d"
    TEXT_C = "#e6edf3"
    TEXT_SEC = "#94a3b8"
    TEXT_MUT = "#64748b"
    BLUE = "#3b82f6"
    RED = "#e8002d"
    GREEN = "#22c55e"

    fig = plt.figure(figsize=(16, 8), dpi=200, facecolor=BG_DARK)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.6, 1], hspace=0.08,
                          left=0.06, right=0.97, top=0.88, bottom=0.08)

    ax_spd = fig.add_subplot(gs[0])
    ax_dlt = fig.add_subplot(gs[1], sharex=ax_spd)

    for ax in (ax_spd, ax_dlt):
        ax.set_facecolor(BG_PANEL)
        ax.tick_params(colors=TEXT_C, labelsize=8)
        ax.yaxis.label.set_color(TEXT_C)
        ax.xaxis.label.set_color(TEXT_C)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_C)
        ax.grid(color=GRID_C, linewidth=0.4, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)

    # corner markers
    corner_labels = [("T1 Grande", 295), ("Roggia", 680), ("Lesmo 1", 1430),
                     ("Lesmo 2", 1650), ("Ascari", 3450), ("Parabolica", 4400)]
    for ax in (ax_spd, ax_dlt):
        for label, dist in corner_labels:
            ax.axvline(dist, color=GRID_C, linewidth=0.8, linestyle=":", alpha=0.55, zorder=1)

    # corner labels on speed panel
    for label, dist in corner_labels:
        ax_spd.text(dist, 355, label, color=TEXT_MUT, fontsize=5.5,
                    ha="center", va="top", alpha=0.8, fontfamily="monospace")

    # speed traces
    ax_spd.plot(d_ver, v_ver, color=BLUE, linewidth=1.2,
                label=f"VER  {_format_lap(lap_ver)}", zorder=3)
    ax_spd.plot(d_sai, v_sai, color=RED, linewidth=1.2, alpha=0.85,
                label=f"SAI  {_format_lap(lap_sai)}", zorder=3)
    ax_spd.set_ylabel("Speed [km/h]", fontsize=9, labelpad=6)
    ax_spd.set_ylim(60, 370)
    ax_spd.yaxis.set_minor_locator(MultipleLocator(25))
    ax_spd.tick_params(labelbottom=False)
    ax_spd.legend(loc="upper right", framealpha=0, fontsize=9,
                  labelcolor=TEXT_C, handlelength=1.6)

    # delta
    ax_dlt.axhline(0, color=TEXT_SEC, linewidth=0.9, linestyle="-", zorder=2, alpha=0.8)
    ax_dlt.plot(d_ver, delta, color=TEXT_C, linewidth=0.6, zorder=3, alpha=0.5)
    ax_dlt.fill_between(d_ver, 0, delta, where=(delta >= 0), interpolate=True,
                        color=GREEN, alpha=0.45, label="SAI advantage", zorder=2)
    ax_dlt.fill_between(d_ver, 0, delta, where=(delta < 0), interpolate=True,
                        color=BLUE, alpha=0.45, label="VER advantage", zorder=2)
    ax_dlt.set_ylabel("dt [s]", fontsize=9, labelpad=6)
    ax_dlt.set_xlabel("Distance [m]", fontsize=9, labelpad=6)
    ax_dlt.legend(loc="lower right", framealpha=0, fontsize=8,
                  labelcolor=TEXT_C, handlelength=1.4)

    # pole gap box
    pole = "VER" if gap < 0 else "SAI"
    anno_color = BLUE if pole == "VER" else RED
    ax_spd.text(
        0.02, 0.06,
        f"POLE GAP\nVER: {_format_lap(lap_ver)}\nSAI: {_format_lap(lap_sai)}\ndt {abs(gap):.3f}s  {pole}",
        transform=ax_spd.transAxes, fontsize=8.5, color=TEXT_C,
        verticalalignment="bottom",
        bbox=dict(boxstyle="round,pad=0.6", facecolor=BG_PANEL,
                  edgecolor=anno_color, linewidth=1.4, alpha=0.92),
        fontfamily="monospace", zorder=10,
    )

    # title
    fig.text(0.06, 0.93, "DIFFERENTIAL TELEMETRY ANALYSIS",
             color=TEXT_C, fontsize=13, fontweight="bold",
             fontfamily="monospace", va="bottom")
    fig.text(0.06, 0.905,
             "2023 Monza Q  |  VER vs SAI  |  Fastest Laps",
             color=TEXT_SEC, fontsize=8.5, va="bottom", fontfamily="monospace")
    fig.add_artist(plt.Line2D(
        [0.06, 0.97], [0.895, 0.895],
        transform=fig.transFigure, color=GRID_C, linewidth=0.8))

    fig.text(0.97, 0.01, "f1-digital-twin-monza | data: FastF1 + FIA",
             color=GRID_C, fontsize=6.5, ha="right", fontfamily="monospace")

    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  -> {out}")


def generate_delta_detail(out="results/delta_detail.png"):
    """Zoomed delta trace showing corner-by-corner gains."""
    d_ver, v_ver = _build_speed_profile(CORNERS, TRACK_LENGTH, seed=42)
    corners_sai = [
        ("T1 Grande", 295, 83), ("T2 Grande", 370, 73),
        ("Roggia", 680, 77), ("Roggia exit", 750, 88),
        ("Lesmo 1", 1430, 190), ("Lesmo 2", 1650, 170),
        ("Ascari entry", 3450, 186), ("Ascari mid", 3560, 182),
        ("Ascari exit", 3640, 196), ("Parabolica", 4400, 162),
    ]
    d_sai, v_sai = _build_speed_profile(corners_sai, TRACK_LENGTH, seed=99)
    t_ver = _speed_to_time(d_ver, v_ver)
    t_sai = _speed_to_time(d_sai, v_sai)
    delta = t_ver - t_sai

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

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.fill_between(d_ver, 0, delta, where=(delta >= 0), interpolate=True,
                    color="#22c55e", alpha=0.3, label="SAI faster")
    ax.fill_between(d_ver, 0, delta, where=(delta < 0), interpolate=True,
                    color="#3b82f6", alpha=0.3, label="VER faster")
    ax.plot(d_ver, delta, color="#333333", linewidth=0.8)
    ax.axhline(0, color="#999999", linewidth=0.5, linestyle="--")

    corners_main = [("T1", 295), ("Roggia", 680), ("Lesmo 1", 1430),
                    ("Lesmo 2", 1650), ("Ascari", 3450), ("Parabolica", 4400)]
    for name, pos in corners_main:
        ax.axvline(pos, color="#cccccc", linewidth=0.6, linestyle=":", alpha=0.7)
        ax.text(pos, ax.get_ylim()[0], f" {name}", fontsize=7, color="#888888",
                va="bottom", rotation=90)

    ax.set_xlabel("distance [m]")
    ax.set_ylabel("dt [s] (neg = VER ahead)")
    ax.set_title("cumulative time delta: VER vs SAI, Monza 2023 Q")
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out}")


if __name__ == "__main__":
    print("Generating example outputs with synthetic telemetry...")
    generate_chart()
    generate_delta_detail()
    print("Done.")
