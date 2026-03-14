"""
dashboard.py
Streamlit app for Monza T1 braking deceleration analysis.
Fetches 2023 Monza Q telemetry via FastF1, computes longitudinal
deceleration (a = dv/dt), and displays a dual-axis chart comparing
VER vs SAI through the Turn 1 braking zone.
"""

import streamlit as st
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d
import fastf1
import fastf1.plotting as fp

st.set_page_config(page_title="Monza T1 Braking", layout="wide")

T1_ENTRY = 600
T1_EXIT = 1050


@st.cache_data(ttl=3600)
def load_telemetry():
    """Fetch real qualifying telemetry and compute deceleration."""
    session = fastf1.get_session(2023, "Monza", "Q")
    session.load()

    ver_lap = session.laps.pick_drivers("VER").pick_fastest()
    sai_lap = session.laps.pick_drivers("SAI").pick_fastest()

    ver_tel = ver_lap.get_car_data().add_distance()
    sai_tel = sai_lap.get_car_data().add_distance()

    ver_color = fp.get_team_color(ver_lap["Team"], session=session)
    sai_color = fp.get_team_color(sai_lap["Team"], session=session)

    def add_decel(df):
        d = df.copy()
        d["ElapsedSec"] = d["SessionTime"].dt.total_seconds()
        d["Speed_ms"] = d["Speed"] * (1000.0 / 3600.0)
        dt = np.gradient(d["ElapsedSec"].values)
        dv = np.gradient(d["Speed_ms"].values)
        dt[dt == 0] = np.nan
        raw_accel = dv / dt
        d["Accel_G"] = raw_accel / 9.81
        d["Accel_G"] = d["Accel_G"].interpolate(method="nearest").bfill().ffill()
        return d

    ver_tel = add_decel(ver_tel)
    sai_tel = add_decel(sai_tel)

    def zone(df):
        return df[(df["Distance"] >= T1_ENTRY) & (df["Distance"] <= T1_EXIT)].copy()

    ver_z = zone(ver_tel)
    sai_z = zone(sai_tel)

    def brake_pt(df, threshold=-0.5):
        heavy = df[df["Accel_G"] < threshold]
        if len(heavy) == 0:
            return None
        return float(heavy["Distance"].iloc[0])

    return {
        "ver_z": ver_z,
        "sai_z": sai_z,
        "ver_color": ver_color,
        "sai_color": sai_color,
        "ver_bp": brake_pt(ver_z),
        "sai_bp": brake_pt(sai_z),
        "ver_peak": float(ver_z["Accel_G"].min()),
        "sai_peak": float(sai_z["Accel_G"].min()),
    }


def make_chart(d):
    """Dual-axis chart: Speed + Deceleration through T1."""
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
    ax_spd.plot(d["ver_z"]["Distance"], d["ver_z"]["Speed"],
                color=d["ver_color"], lw=1.8, label="VER", alpha=0.95)
    ax_spd.plot(d["sai_z"]["Distance"], d["sai_z"]["Speed"],
                color=d["sai_color"], lw=1.8, label="SAI", alpha=0.85)

    if d["ver_bp"]:
        ax_spd.axvline(d["ver_bp"], color=d["ver_color"], ls="--", lw=1, alpha=0.6)
        ax_spd.text(d["ver_bp"] + 5, 120, f"VER brake\n{d['ver_bp']:.0f}m",
                    fontsize=7, color=d["ver_color"], fontfamily="monospace")
    if d["sai_bp"]:
        ax_spd.axvline(d["sai_bp"], color=d["sai_color"], ls="--", lw=1, alpha=0.6)
        ax_spd.text(d["sai_bp"] + 5, 150, f"SAI brake\n{d['sai_bp']:.0f}m",
                    fontsize=7, color=d["sai_color"], fontfamily="monospace")

    ax_spd.set_ylabel("Speed [km/h]", fontsize=10, color=txt)
    ax_spd.tick_params(colors=muted, labelsize=8)
    ax_spd.legend(loc="upper right", framealpha=0, fontsize=9, labelcolor=txt)
    ax_spd.grid(color=grid_c, lw=0.3, alpha=0.5)
    for s in ax_spd.spines.values():
        s.set_edgecolor(grid_c)

    # deceleration panel
    ax_dec.set_facecolor(panel)
    sm_v = uniform_filter1d(d["ver_z"]["Accel_G"].values, size=5)
    sm_s = uniform_filter1d(d["sai_z"]["Accel_G"].values, size=5)

    ax_dec.plot(d["ver_z"]["Distance"].values, sm_v, color=d["ver_color"],
                lw=1.8, label="VER decel", alpha=0.95)
    ax_dec.plot(d["sai_z"]["Distance"].values, sm_s, color=d["sai_color"],
                lw=1.8, label="SAI decel", alpha=0.85)
    ax_dec.axhline(0, color=muted, lw=0.6)
    ax_dec.fill_between(d["ver_z"]["Distance"].values, 0, sm_v,
                        where=(sm_v < 0), alpha=0.15, color=d["ver_color"])
    ax_dec.fill_between(d["sai_z"]["Distance"].values, 0, sm_s,
                        where=(sm_s < 0), alpha=0.12, color=d["sai_color"])

    ax_dec.text(0.02, 0.06,
                f"Peak: VER {d['ver_peak']:.2f}G  |  SAI {d['sai_peak']:.2f}G",
                transform=ax_dec.transAxes, fontsize=8, color=txt, fontfamily="monospace",
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
             "Speed and longitudinal deceleration (a = dv/dt)  |  VER vs SAI",
             ha="center", color=muted, fontsize=9, fontfamily="monospace")

    return fig


def main():
    st.title("Monza T1 | Braking Deceleration")
    st.caption("2023 Italian GP Qualifying  /  VER vs SAI  /  Real FIA telemetry via FastF1")

    with st.spinner("Loading telemetry from FIA servers..."):
        d = load_telemetry()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("VER brake point", f"{d['ver_bp']:.0f} m" if d["ver_bp"] else "n/a")
    c2.metric("SAI brake point", f"{d['sai_bp']:.0f} m" if d["sai_bp"] else "n/a")
    c3.metric("VER peak decel", f"{d['ver_peak']:.2f} G")
    c4.metric("SAI peak decel", f"{d['sai_peak']:.2f} G")

    if d["ver_bp"] and d["sai_bp"]:
        diff = abs(d["sai_bp"] - d["ver_bp"])
        later = "VER" if d["ver_bp"] > d["sai_bp"] else "SAI"
        st.info(f"**{later}** brakes **{diff:.0f} m later** into Turn 1.")

    fig = make_chart(d)
    st.pyplot(fig, use_container_width=True)

    with st.expander("Raw telemetry (T1 zone)"):
        t1, t2 = st.tabs(["VER", "SAI"])
        with t1:
            st.dataframe(
                d["ver_z"][["Distance", "Speed", "Accel_G"]].rename(
                    columns={"Accel_G": "Accel [G]"}),
                use_container_width=True,
            )
        with t2:
            st.dataframe(
                d["sai_z"][["Distance", "Speed", "Accel_G"]].rename(
                    columns={"Accel_G": "Accel [G]"}),
                use_container_width=True,
            )

    st.caption("Data: FIA via FastF1  /  Physics: a = dv/dt, expressed in G (9.81 m/s2)")


if __name__ == "__main__":
    main()
