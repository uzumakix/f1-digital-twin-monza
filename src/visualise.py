"""
Visualisation: two-panel dark-mode telemetry chart.

Renders speed traces and cumulative time delta against track distance,
with configurable corner markers and theme colours.
"""

from __future__ import annotations

import logging
from typing import List, Tuple

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from src.config import Config, ThemeConfig
from src.resample import ResampledData

matplotlib.use("Agg")
logger = logging.getLogger(__name__)


def _format_lap_time(seconds: float) -> str:
    """Convert raw seconds to 'M:SS.mmm' string."""
    m, s = divmod(seconds, 60)
    return f"{int(m)}:{s:06.3f}"


def _apply_theme(ax: plt.Axes, theme: ThemeConfig) -> None:
    """Apply dark-mode styling to an axes object."""
    ax.set_facecolor(theme.bg_panel)
    ax.tick_params(colors=theme.text_color, labelsize=8)
    ax.yaxis.label.set_color(theme.text_color)
    ax.xaxis.label.set_color(theme.text_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(theme.grid_color)
    ax.grid(color=theme.grid_color, linewidth=0.4, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)


def _draw_corners(
    ax: plt.Axes,
    corners: List[Tuple[str, int]],
    track_length: float,
    theme: ThemeConfig,
) -> None:
    """Overlay corner position markers as faint vertical lines."""
    for label, dist in corners:
        if dist < track_length:
            ax.axvline(
                dist, color=theme.grid_color, linewidth=0.8,
                linestyle=":", alpha=0.55, zorder=1,
            )
            ax.text(
                dist, ax.get_ylim()[1] * 0.97, label,
                color=theme.text_muted, fontsize=5.5, ha="center",
                va="top", alpha=0.8, fontfamily="monospace",
            )


def render_chart(
    data: ResampledData,
    cfg: Config,
) -> str:
    """Render two-panel speed + delta chart and save to disk.

    Args:
        data: Resampled telemetry data.
        cfg: Full configuration object.

    Returns:
        Path to the saved chart file.
    """
    logger.info("Rendering chart")
    theme = cfg.theme
    driver_a = cfg.drivers.reference
    driver_b = cfg.drivers.comparison

    d = data.d
    delta = data.delta
    t_a_str = _format_lap_time(data.t_a[-1])
    t_b_str = _format_lap_time(data.t_b[-1])
    gap = data.t_a[-1] - data.t_b[-1]

    # Figure
    fig = plt.figure(figsize=(16, 8), dpi=cfg.output.dpi, facecolor=theme.bg_dark)
    gs = fig.add_gridspec(
        2, 1, height_ratios=[1.6, 1], hspace=0.08,
        left=0.06, right=0.97, top=0.88, bottom=0.08,
    )

    ax_spd = fig.add_subplot(gs[0])
    ax_dlt = fig.add_subplot(gs[1], sharex=ax_spd)
    _apply_theme(ax_spd, theme)
    _apply_theme(ax_dlt, theme)

    # Panel 1: Speed traces
    ax_spd.plot(
        d, data.v_a, color=theme.speed_a, linewidth=1.2,
        label=f"{driver_a}  {t_a_str}", zorder=3,
    )
    ax_spd.plot(
        d, data.v_b, color=theme.speed_b, linewidth=1.2,
        alpha=0.85, label=f"{driver_b}  {t_b_str}", zorder=3,
    )
    ax_spd.set_ylabel("Speed [km/h]", fontsize=9, labelpad=6)
    ax_spd.set_ylim(60, 370)
    ax_spd.yaxis.set_minor_locator(MultipleLocator(25))
    ax_spd.tick_params(labelbottom=False)
    ax_spd.legend(
        loc="upper right", framealpha=0, fontsize=9,
        labelcolor=theme.text_color, handlelength=1.6,
    )
    _draw_corners(ax_spd, cfg.corners, d[-1], theme)

    # Panel 2: Time delta
    ax_dlt.axhline(
        0, color=theme.zero_line, linewidth=0.9,
        linestyle="-", zorder=2, alpha=0.8,
    )
    ax_dlt.plot(d, delta, color=theme.text_color, linewidth=0.6, zorder=3, alpha=0.5)
    ax_dlt.fill_between(
        d, 0, delta, where=(delta >= 0), interpolate=True,
        color=theme.fill_b, alpha=0.45, label=f"{driver_b} advantage", zorder=2,
    )
    ax_dlt.fill_between(
        d, 0, delta, where=(delta < 0), interpolate=True,
        color=theme.fill_a, alpha=0.45, label=f"{driver_a} advantage", zorder=2,
    )
    ax_dlt.set_ylabel("dt [s]", fontsize=9, labelpad=6)
    ax_dlt.set_xlabel("Distance [m]", fontsize=9, labelpad=6)
    ax_dlt.legend(
        loc="lower right", framealpha=0, fontsize=8,
        labelcolor=theme.text_color, handlelength=1.4,
    )
    _draw_corners(ax_dlt, cfg.corners, d[-1], theme)

    # Pole gap annotation
    pole = driver_a if gap < 0 else driver_b
    anno_color = theme.speed_a if pole == driver_a else theme.speed_b
    ax_spd.text(
        0.02, 0.06,
        f"POLE GAP\n{driver_a}: {t_a_str}\n{driver_b}: {t_b_str}\ndt {abs(gap):.3f}s  {pole}",
        transform=ax_spd.transAxes, fontsize=8.5, color=theme.text_color,
        verticalalignment="bottom",
        bbox=dict(
            boxstyle="round,pad=0.6", facecolor=theme.bg_panel,
            edgecolor=anno_color, linewidth=1.4, alpha=0.92,
        ),
        fontfamily="monospace", zorder=10,
    )

    # Title block
    session_label = f"{cfg.session.year} {cfg.session.circuit} {cfg.session.type}"
    fig.text(
        0.06, 0.93, "DIFFERENTIAL TELEMETRY ANALYSIS",
        color=theme.text_color, fontsize=13, fontweight="bold",
        fontfamily="monospace", va="bottom",
    )
    fig.text(
        0.06, 0.905,
        f"{session_label}  |  {driver_a} vs {driver_b}  |  Fastest Laps",
        color=theme.text_secondary, fontsize=8.5, va="bottom",
        fontfamily="monospace",
    )
    fig.add_artist(plt.Line2D(
        [0.06, 0.97], [0.895, 0.895],
        transform=fig.transFigure, color=theme.grid_color, linewidth=0.8,
    ))

    # Watermark
    fig.text(
        0.97, 0.01, "f1-digital-twin-monza | data: FastF1 + FIA",
        color=theme.grid_color, fontsize=6.5, ha="right", fontfamily="monospace",
    )

    output_path = cfg.output.filename
    fig.savefig(output_path, dpi=cfg.output.dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("Chart saved: %s", output_path)
    return output_path
