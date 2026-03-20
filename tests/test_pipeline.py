import pytest
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '.')

from pipeline import compute_deceleration, extract_braking_zone, find_brake_point


class TestComputeDeceleration:
    def test_accel_values_negative(self, sample_telemetry):
        result = compute_deceleration(sample_telemetry)
        # linear decel from 300 to 100 km/h, all values should be negative
        accel = result['Accel_G'].dropna()
        assert (accel < 0).all(), "expected all negative accel during braking"

    def test_accel_magnitude_reasonable(self, sample_telemetry):
        result = compute_deceleration(sample_telemetry)
        accel = result['Accel_G'].dropna()
        # typical F1 braking is 1-6 G, our synthetic data should stay under 10
        assert (accel.abs() > 0.1).all(), "accel too small to be real braking"
        assert (accel.abs() < 10).all(), "accel exceeds physically plausible range"

    def test_speed_ms_conversion(self, sample_telemetry):
        result = compute_deceleration(sample_telemetry)
        expected_ms = sample_telemetry['Speed'] * 1000 / 3600
        np.testing.assert_allclose(
            result['Speed_ms'].values, expected_ms.values, rtol=1e-6
        )

    def test_output_has_required_columns(self, sample_telemetry):
        result = compute_deceleration(sample_telemetry)
        for col in ['Speed_ms', 'Accel_G']:
            assert col in result.columns


class TestExtractBrakingZone:
    def test_filters_by_distance(self, sample_telemetry):
        df = compute_deceleration(sample_telemetry)
        d_min = df['Distance'].min()
        d_max = df['Distance'].max()
        mid = (d_min + d_max) / 2

        zone = extract_braking_zone(df, d_min, mid)
        assert len(zone) > 0
        assert zone['Distance'].max() <= mid
        assert zone['Distance'].min() >= d_min

    def test_empty_when_range_outside_data(self, sample_telemetry):
        df = compute_deceleration(sample_telemetry)
        zone = extract_braking_zone(df, 0, 10)  # way before data starts at 600
        assert len(zone) == 0


class TestFindBrakePoint:
    def test_finds_known_threshold_crossing(self):
        # build data where decel crosses -2G exactly at distance=700
        n = 50
        dist = np.linspace(650, 750, n)
        accel = np.linspace(0, -4, n)  # crosses -2G at midpoint
        df = pd.DataFrame({'Distance': dist, 'Accel_G': accel})

        bp = find_brake_point(df, threshold_g=-2.0)
        assert bp is not None
        assert 690 < bp < 710, f"brake point {bp} not near expected ~700"

    def test_returns_none_when_no_heavy_braking(self):
        n = 50
        dist = np.linspace(650, 750, n)
        accel = np.full(n, -0.5)  # gentle decel, never hits threshold
        df = pd.DataFrame({'Distance': dist, 'Accel_G': accel})

        bp = find_brake_point(df, threshold_g=-2.0)
        assert bp is None

    def test_returns_none_on_empty_input(self):
        df = pd.DataFrame({'Distance': [], 'Accel_G': []})
        bp = find_brake_point(df, threshold_g=-2.0)
        assert bp is None
