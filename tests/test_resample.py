"""Tests for the resampling module."""

import numpy as np
import pytest

from src.resample import resample_to_distance_domain, build_interpolator


class TestBuildInterpolator:
    def test_exact_values_at_known_points(self, mock_telemetry):
        tel = mock_telemetry()
        f = build_interpolator(tel, "Speed")
        result = f(tel["Distance"].values[50])
        expected = tel["Speed"].values[50]
        assert abs(result - expected) < 1e-6

    def test_handles_duplicate_distances(self, mock_telemetry):
        tel = mock_telemetry()
        tel.loc[10, "Distance"] = tel.loc[9, "Distance"]
        f = build_interpolator(tel, "Speed")
        assert f(100.0) is not None

    def test_extrapolation_clamps_to_boundary(self, mock_telemetry):
        tel = mock_telemetry(max_dist=1000)
        f = build_interpolator(tel, "Speed")
        result = f(2000.0)
        assert abs(result - tel["Speed"].values[-1]) < 1e-6

    def test_interpolation_between_points(self, mock_telemetry):
        tel = mock_telemetry(n_points=10, max_dist=100)
        f = build_interpolator(tel, "Speed")
        mid = 55.0  # Between grid points
        result = f(mid)
        assert tel["Speed"].min() <= result <= tel["Speed"].max()


class TestResample:
    def test_output_type(self, mock_telemetry):
        tel_a = mock_telemetry()
        tel_b = mock_telemetry()
        data = resample_to_distance_domain(tel_a, tel_b, step=10)
        assert hasattr(data, "d")
        assert hasattr(data, "delta")

    def test_to_dict_keys(self, mock_telemetry):
        tel_a = mock_telemetry()
        tel_b = mock_telemetry()
        data = resample_to_distance_domain(tel_a, tel_b, step=10)
        d = data.to_dict()
        assert set(d.keys()) == {"d", "t_A", "t_B", "v_A", "v_B", "delta"}

    def test_grid_bounded_by_shorter_lap(self, mock_telemetry):
        tel_a = mock_telemetry(max_dist=5000)
        tel_b = mock_telemetry(max_dist=4800)
        data = resample_to_distance_domain(tel_a, tel_b, step=10)
        assert data.d[-1] < 4800

    def test_delta_zero_for_identical_inputs(self, mock_telemetry):
        tel = mock_telemetry()
        data = resample_to_distance_domain(tel, tel.copy(), step=10)
        assert np.allclose(data.delta, 0, atol=1e-10)

    def test_all_arrays_same_length(self, mock_telemetry):
        tel_a = mock_telemetry()
        tel_b = mock_telemetry()
        data = resample_to_distance_domain(tel_a, tel_b, step=5)
        lengths = {len(data.d), len(data.t_a), len(data.t_b),
                   len(data.v_a), len(data.v_b), len(data.delta)}
        assert len(lengths) == 1

    def test_faster_driver_produces_negative_delta(self, mock_telemetry):
        tel_a = mock_telemetry(lap_time=70.0)
        tel_b = mock_telemetry(lap_time=71.0)
        data = resample_to_distance_domain(tel_a, tel_b, step=50)
        assert data.delta[-1] < 0  # A is faster, delta should be negative

    def test_step_size_affects_resolution(self, mock_telemetry):
        tel_a = mock_telemetry()
        tel_b = mock_telemetry()
        fine = resample_to_distance_domain(tel_a, tel_b, step=1)
        coarse = resample_to_distance_domain(tel_a, tel_b, step=100)
        assert len(fine.d) > len(coarse.d)
