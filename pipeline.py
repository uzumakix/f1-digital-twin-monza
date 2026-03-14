"""
pipeline.py
Fetches real 2023 Monza Q telemetry from FastF1 and computes
longitudinal deceleration through the T1 braking zone.

The physics:
    a(t) = dv/dt
    We convert speed from km/h to m/s, then take the numerical
    derivative with respect to elapsed time to get acceleration
    in m/s^2. Divide by 9.81 to express in G.
"""

import numpy as np
import pandas as pd
import fastf1
import fastf1.plotting as fp


# Monza T1 braking zone boundaries (metres from start/finish)
T1_ENTRY = 600
T1_EXIT = 1050


def load_qualifying_telemetry(year=2023, gp="Monza", session_type="Q",
                               driver_a="VER", driver_b="SAI"):
    """Pull real telemetry for two drivers' fastest qualifying laps."""
    session = fastf1.get_session(year, gp, session_type)
    session.load()

    lap_a = session.laps.pick_drivers(driver_a).pick_fastest()
    lap_b = session.laps.pick_drivers(driver_b).pick_fastest()

    tel_a = lap_a.get_car_data().add_distance()
    tel_b = lap_b.get_car_data().add_distance()

    color_a = fp.get_team_color(lap_a["Team"], session=session)
    color_b = fp.get_team_color(lap_b["Team"], session=session)

    return {
        "session": session,
        "lap_a": lap_a, "lap_b": lap_b,
        "tel_a": tel_a, "tel_b": tel_b,
        "driver_a": driver_a, "driver_b": driver_b,
        "color_a": color_a, "color_b": color_b,
    }


def compute_deceleration(tel: pd.DataFrame) -> pd.DataFrame:
    """
    Take raw telemetry and compute longitudinal deceleration.

    Physics:
        v [km/h] -> v [m/s] = v * (1000/3600)
        a [m/s^2] = dv/dt
        a [G] = a / 9.81

    We use np.gradient for the numerical derivative, which gives
    central differences (second-order accurate) at interior points.
    """
    df = tel.copy()

    # elapsed time in seconds from session start
    df["ElapsedSeconds"] = (
        df["SessionTime"].dt.total_seconds()
        if hasattr(df["SessionTime"].iloc[0], "total_seconds")
        else df["SessionTime"]
    )

    # speed in m/s
    df["Speed_ms"] = df["Speed"] * (1000.0 / 3600.0)

    # numerical derivative: a = dv/dt
    dt = np.gradient(df["ElapsedSeconds"].values)
    dv = np.gradient(df["Speed_ms"].values)

    # avoid division by zero on duplicate timestamps
    dt[dt == 0] = np.nan
    df["Accel_ms2"] = dv / dt
    df["Accel_G"] = df["Accel_ms2"] / 9.81

    # fill any NaN from zero-dt with nearest value
    df["Accel_ms2"] = df["Accel_ms2"].interpolate(method="nearest").bfill().ffill()
    df["Accel_G"] = df["Accel_G"].interpolate(method="nearest").bfill().ffill()

    return df


def extract_braking_zone(df: pd.DataFrame,
                          d_start=T1_ENTRY, d_end=T1_EXIT) -> pd.DataFrame:
    """Slice telemetry to the T1 braking zone by distance."""
    mask = (df["Distance"] >= d_start) & (df["Distance"] <= d_end)
    return df.loc[mask].copy()


def find_brake_point(df_zone: pd.DataFrame, threshold_g=-0.5):
    """
    Find the distance where the driver first exceeds the
    deceleration threshold (i.e., starts heavy braking).
    """
    heavy = df_zone[df_zone["Accel_G"] < threshold_g]
    if len(heavy) == 0:
        return None
    return heavy["Distance"].iloc[0]


def run_pipeline():
    """Full pipeline: ingest -> compute -> extract -> return."""
    data = load_qualifying_telemetry()

    # compute deceleration for both drivers
    data["tel_a"] = compute_deceleration(data["tel_a"])
    data["tel_b"] = compute_deceleration(data["tel_b"])

    # extract T1 braking zone
    data["zone_a"] = extract_braking_zone(data["tel_a"])
    data["zone_b"] = extract_braking_zone(data["tel_b"])

    # find where each driver starts heavy braking
    data["brake_point_a"] = find_brake_point(data["zone_a"])
    data["brake_point_b"] = find_brake_point(data["zone_b"])

    # peak deceleration in zone
    data["peak_decel_a"] = data["zone_a"]["Accel_G"].min()
    data["peak_decel_b"] = data["zone_b"]["Accel_G"].min()

    return data


if __name__ == "__main__":
    data = run_pipeline()
    da, db = data["driver_a"], data["driver_b"]
    print(f"\n=== Monza 2023 Q — T1 Braking Analysis ===")
    print(f"{da} brake point: {data['brake_point_a']:.0f} m")
    print(f"{db} brake point: {data['brake_point_b']:.0f} m")
    print(f"{da} peak decel:  {data['peak_decel_a']:.2f} G")
    print(f"{db} peak decel:  {data['peak_decel_b']:.2f} G")
