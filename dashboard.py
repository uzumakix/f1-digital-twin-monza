"""
dashboard.py
Streamlit app for Monza T1 braking deceleration analysis.
Pulls real 2023 Monza Q telemetry via pipeline.py, displays a
dual-axis chart of speed and longitudinal deceleration (a = dv/dt)
through the Turn 1 braking zone.
"""

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d
from pipeline import run_pipeline

st.set_page_config(page_title="Monza T1 Braking", layout="wide")


@st.cache_data(ttl=3600)
def get_data():
    return run_pipeline()


def make_chart(data):
    """Dual-axis chart: Speed + Deceleration through T1."""
    zone_a = data["zone_a"]
    zone_b = data["zone_b"]
    da, db = data["driver_a"], data["driver_b"]
    ca, cb = data["color_a"], data["color_b"]
    bp_a, bp_b = data["brake_point_a"], data["brake_point_b"]
    peak_a, peak_b = data["peak_decel_a"], data["peak_decel_b"]

    bg = "#0e1117"
    panel = "#1a1a2e"
    grid_c = "#2a2a4a"
    txt = "#e0e0e0"
    muted = "#888888"

    fig, (ax_spd, ax_dec) = plt.subplots(
        2, 1, figsize=(14, 8), sharex=True, facecolor=bg,
        gridspec_kw={"height_ratios": [1, 1.2], "hspace": 0.08},
    )

    # speed panel
    ax_spd.set_facecolor(panel)
    ax_spd.plot(zone_a["Distance"], zone_a["Speed"],
                color=ca, lw=1.8, label=da, alpha=0.95)
    ax_spd.plot(zone_b["Distance"], zone_b["Speed"],
                color=cb, lw=1.8, label=db, alpha=0.85)

    if bp_a is not None:
        ax_spd.axvline(bp_a, color=ca, ls="--", lw=1, alpha=0.6)
        ax_spd.text(bp_a - 30, 130, f"{da} brake\n{bp_a:.0f}m",
                    fontsize=7, color=ca, fontfamily="monospace", ha="right")
    if bp_b is not None:
        ax_spd.axvline(bp_b, color=cb, ls="--", lw=1, alpha=0.6)
        ax_spd.text(bp_b + 5, 160, f"{db} brake\n{bp_b:.0f}m",
                    fontsize=7, color=cb, fontfamily="monospace")

    ax_spd.set_ylabel("Speed [km/h]", fontsize=10, color=txt)
    ax_spd.tick_params(colors=muted, labelsize=8)
    ax_spd.legend(loc="upper right", framealpha=0, fontsize=9, labelcolor=txt)
    ax_spd.grid(color=grid_c, lw=0.3, alpha=0.5)
    for s in ax_spd.spines.values():
        s.set_edgecolor(grid_c)

    # deceleration panel
    ax_dec.set_facecolor(panel)
    smooth_a = uniform_filter1d(zone_a["Accel_G"].values, size=5)
    smooth_b = uniform_filter1d(zone_b["Accel_G"].values, size=5)

    ax_dec.plot(zone_a["Distance"].values, smooth_a, color=ca,
                lw=1.8, label=f"{da} decel", alpha=0.95)
    ax_dec.plot(zone_b["Distance"].values, smooth_b, color=cb,
                lw=1.8, label=f"{db} decel", alpha=0.85)
    ax_dec.axhline(0, color=muted, lw=0.6)
    ax_dec.fill_between(zone_a["Distance"].values, 0, smooth_a,
                        where=(smooth_a < 0), alpha=0.15, color=ca)
    ax_dec.fill_between(zone_b["Distance"].values, 0, smooth_b,
                        where=(smooth_b < 0), alpha=0.12, color=cb)

    ax_dec.text(0.02, 0.06,
                f"Peak: {da} {peak_a:.2f}G  |  {db} {peak_b:.2f}G",
                transform=ax_dec.transAxes, fontsize=8, color=txt,
                fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.4", fc=panel, ec=grid_c, lw=0.8))

    ax_dec.set_ylabel("Longitudinal Accel [G]", fontsize=10, color=txt)
    ax_dec.set_xlabel("Distance [m]", fontsize=10, color=txt)
    ax_dec.tick_params(colors=muted, labelsize=8)
    ax_dec.legend(loc="lower right", framealpha=0, fontsize=8, labelcolor=txt)
    ax_dec.grid(color=grid_c, lw=0.3, alpha=0.5)
    for s in ax_dec.spines.values():
        s.set_edgecolor(grid_c)

    fig.suptitle("MONZA 2023 Q  |  TURN 1 BRAKING ZONE",
                 color=txt, fontsize=13, fontweight="bold",
                 fontfamily="monospace", y=0.96)
    fig.text(0.5, 0.925,
             f"Speed and longitudinal deceleration (a = dv/dt)  |  {da} vs {db}",
             ha="center", color=muted, fontsize=9, fontfamily="monospace")

    return fig


def main():
    st.title("Monza T1 | Braking Deceleration")
    st.caption("2023 Italian GP Qualifying  /  VER vs SAI  /  Real FIA telemetry via FastF1")

    with st.spinner("Loading telemetry from FIA servers..."):
        data = get_data()

    da, db = data["driver_a"], data["driver_b"]
    bp_a, bp_b = data["brake_point_a"], data["brake_point_b"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{da} brake point", f"{bp_a:.0f} m" if bp_a else "n/a")
    c2.metric(f"{db} brake point", f"{bp_b:.0f} m" if bp_b else "n/a")
    c3.metric(f"{da} peak decel", f"{data['peak_decel_a']:.2f} G")
    c4.metric(f"{db} peak decel", f"{data['peak_decel_b']:.2f} G")

    if bp_a and bp_b:
        diff = abs(bp_b - bp_a)
        later = da if bp_a > bp_b else db
        st.info(f"**{later}** brakes **{diff:.0f} m later** into Turn 1.")

    fig = make_chart(data)
    st.pyplot(fig, use_container_width=True)

    with st.expander("Raw telemetry (T1 zone)"):
        tab1, tab2 = st.tabs([da, db])
        with tab1:
            st.dataframe(
                data["zone_a"][["Distance", "Speed", "Accel_ms2", "Accel_G"]]
                .rename(columns={"Accel_ms2": "Accel [m/s2]", "Accel_G": "Accel [G]"}),
                use_container_width=True,
            )
        with tab2:
            st.dataframe(
                data["zone_b"][["Distance", "Speed", "Accel_ms2", "Accel_G"]]
                .rename(columns={"Accel_ms2": "Accel [m/s2]", "Accel_G": "Accel [G]"}),
                use_container_width=True,
            )

    st.caption("Data: FIA via FastF1  /  Physics: a = dv/dt, expressed in G (9.81 m/s2)")


if __name__ == "__main__":
    main()
