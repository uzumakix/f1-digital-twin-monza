"""
app.py
Streamlit dashboard for Monza T1 braking zone analysis.

Visualises speed and longitudinal deceleration (G-force) through
the Turn 1 braking zone, comparing two qualifying laps side by side.
"""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pipeline import run_pipeline

st.set_page_config(
    page_title="Monza T1 Braking Analysis",
    layout="wide",
)


@st.cache_data(ttl=3600)
def get_data():
    return run_pipeline()


def plot_braking_zone(data):
    """
    Dual-axis plot for the T1 braking zone:
      - Top: Speed (km/h) vs Distance
      - Bottom: Longitudinal deceleration (G) vs Distance
    Both drivers overlaid with team colours.
    """
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

    # --- speed panel ---
    ax1.set_facecolor(panel)
    ax1.plot(zone_a["Distance"], zone_a["Speed"], color=ca,
             linewidth=1.8, label=da, alpha=0.95)
    ax1.plot(zone_b["Distance"], zone_b["Speed"], color=cb,
             linewidth=1.8, label=db, alpha=0.85)

    # mark brake points
    if bp_a is not None:
        ax1.axvline(bp_a, color=ca, linestyle="--", linewidth=1, alpha=0.6)
        ax1.text(bp_a + 3, ax1.get_ylim()[0] + 5,
                 f"{da} brake\n{bp_a:.0f}m", fontsize=7, color=ca,
                 fontfamily="monospace", va="bottom")
    if bp_b is not None:
        ax1.axvline(bp_b, color=cb, linestyle="--", linewidth=1, alpha=0.6)
        ax1.text(bp_b + 3, ax1.get_ylim()[0] + 25,
                 f"{db} brake\n{bp_b:.0f}m", fontsize=7, color=cb,
                 fontfamily="monospace", va="bottom")

    ax1.set_ylabel("Speed [km/h]", fontsize=10, color=text_c)
    ax1.tick_params(colors=muted, labelsize=8)
    ax1.legend(loc="upper right", framealpha=0, fontsize=9,
               labelcolor=text_c)
    ax1.grid(color=grid_c, linewidth=0.3, alpha=0.5)
    for spine in ax1.spines.values():
        spine.set_edgecolor(grid_c)

    # --- deceleration panel ---
    ax2.set_facecolor(panel)

    # smooth the deceleration slightly for readability
    from scipy.ndimage import uniform_filter1d
    smooth_a = uniform_filter1d(zone_a["Accel_G"].values, size=5)
    smooth_b = uniform_filter1d(zone_b["Accel_G"].values, size=5)

    ax2.plot(zone_a["Distance"].values, smooth_a, color=ca,
             linewidth=1.8, label=f"{da} decel", alpha=0.95)
    ax2.plot(zone_b["Distance"].values, smooth_b, color=cb,
             linewidth=1.8, label=f"{db} decel", alpha=0.85)

    ax2.axhline(0, color=muted, linewidth=0.6, linestyle="-")
    ax2.fill_between(zone_a["Distance"].values, 0, smooth_a,
                     where=(smooth_a < 0), alpha=0.15, color=ca)
    ax2.fill_between(zone_b["Distance"].values, 0, smooth_b,
                     where=(smooth_b < 0), alpha=0.12, color=cb)

    # annotate peak deceleration
    peak_a = data["peak_decel_a"]
    peak_b = data["peak_decel_b"]
    ax2.text(0.02, 0.06,
             f"Peak decel: {da} {peak_a:.2f}G  |  {db} {peak_b:.2f}G",
             transform=ax2.transAxes, fontsize=8, color=text_c,
             fontfamily="monospace",
             bbox=dict(boxstyle="round,pad=0.4", fc=panel, ec=grid_c, lw=0.8))

    ax2.set_ylabel("Longitudinal Accel [G]", fontsize=10, color=text_c)
    ax2.set_xlabel("Distance [m]", fontsize=10, color=text_c)
    ax2.tick_params(colors=muted, labelsize=8)
    ax2.legend(loc="lower right", framealpha=0, fontsize=8,
               labelcolor=text_c)
    ax2.grid(color=grid_c, linewidth=0.3, alpha=0.5)
    for spine in ax2.spines.values():
        spine.set_edgecolor(grid_c)

    # title
    fig.suptitle("MONZA 2023 Q  —  TURN 1 BRAKING ZONE",
                 color=text_c, fontsize=13, fontweight="bold",
                 fontfamily="monospace", y=0.96)
    fig.text(0.5, 0.925,
             f"Speed and longitudinal deceleration (a = dv/dt)  |  {da} vs {db}",
             ha="center", color=muted, fontsize=9, fontfamily="monospace")

    return fig


def main():
    st.title("Monza T1 — Braking Deceleration Analysis")
    st.caption("2023 Italian GP Qualifying  ·  VER vs SAI  ·  Real FIA telemetry via FastF1")

    with st.spinner("Loading telemetry from FIA servers..."):
        data = get_data()

    da, db = data["driver_a"], data["driver_b"]
    bp_a, bp_b = data["brake_point_a"], data["brake_point_b"]

    # key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"{da} brake point", f"{bp_a:.0f} m" if bp_a else "—")
    col2.metric(f"{db} brake point", f"{bp_b:.0f} m" if bp_b else "—")
    col3.metric(f"{da} peak decel", f"{data['peak_decel_a']:.2f} G")
    col4.metric(f"{db} peak decel", f"{data['peak_decel_b']:.2f} G")

    if bp_a and bp_b:
        diff = abs(bp_b - bp_a)
        later = da if bp_a > bp_b else db
        st.info(f"**{later}** brakes **{diff:.0f} m later** into Turn 1.")

    # main chart
    fig = plot_braking_zone(data)
    st.pyplot(fig, use_container_width=True)

    # raw data expander
    with st.expander("Raw telemetry (T1 zone)"):
        tab1, tab2 = st.tabs([da, db])
        with tab1:
            st.dataframe(
                data["zone_a"][["Distance", "Speed", "Accel_ms2", "Accel_G"]]
                .rename(columns={"Accel_ms2": "Accel [m/s²]", "Accel_G": "Accel [G]"}),
                use_container_width=True
            )
        with tab2:
            st.dataframe(
                data["zone_b"][["Distance", "Speed", "Accel_ms2", "Accel_G"]]
                .rename(columns={"Accel_ms2": "Accel [m/s²]", "Accel_G": "Accel [G]"}),
                use_container_width=True
            )

    st.caption("Data: FIA via FastF1  ·  Physics: a = dv/dt, expressed in G (9.81 m/s²)")


if __name__ == "__main__":
    main()
