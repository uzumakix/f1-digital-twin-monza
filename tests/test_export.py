"""Tests for the export module."""

import json

import pandas as pd
import pytest

from src.export import export_csv, export_json, OUTPUT_DIR


class TestExportCSV:
    def test_creates_file(self, sample_resampled_data, sample_config, tmp_path, monkeypatch):
        monkeypatch.setattr("src.export.OUTPUT_DIR", tmp_path)
        path = export_csv(sample_resampled_data, sample_config)
        assert path.exists()

    def test_correct_columns(self, sample_resampled_data, sample_config, tmp_path, monkeypatch):
        monkeypatch.setattr("src.export.OUTPUT_DIR", tmp_path)
        path = export_csv(sample_resampled_data, sample_config)
        df = pd.read_csv(path)
        expected = {"distance_m", "speed_VER_kmh", "speed_SAI_kmh",
                    "elapsed_VER_s", "elapsed_SAI_s", "delta_s"}
        assert set(df.columns) == expected

    def test_row_count_matches_data(self, sample_resampled_data, sample_config, tmp_path, monkeypatch):
        monkeypatch.setattr("src.export.OUTPUT_DIR", tmp_path)
        path = export_csv(sample_resampled_data, sample_config)
        df = pd.read_csv(path)
        assert len(df) == len(sample_resampled_data.d)

    def test_float_precision(self, sample_resampled_data, sample_config, tmp_path, monkeypatch):
        monkeypatch.setattr("src.export.OUTPUT_DIR", tmp_path)
        path = export_csv(sample_resampled_data, sample_config)
        with open(path) as f:
            line = f.readlines()[1]  # First data line
        parts = line.strip().split(",")
        # Each value should have at most 4 decimal places
        for part in parts:
            if "." in part:
                assert len(part.split(".")[-1]) <= 4


class TestExportJSON:
    def test_creates_file(self, sample_resampled_data, sample_config, tmp_path, monkeypatch):
        monkeypatch.setattr("src.export.OUTPUT_DIR", tmp_path)
        path = export_json(sample_resampled_data, sample_config)
        assert path.exists()

    def test_has_metadata_and_telemetry(self, sample_resampled_data, sample_config, tmp_path, monkeypatch):
        monkeypatch.setattr("src.export.OUTPUT_DIR", tmp_path)
        path = export_json(sample_resampled_data, sample_config)
        with open(path) as f:
            payload = json.load(f)
        assert "metadata" in payload
        assert "telemetry" in payload

    def test_metadata_point_count(self, sample_resampled_data, sample_config, tmp_path, monkeypatch):
        monkeypatch.setattr("src.export.OUTPUT_DIR", tmp_path)
        path = export_json(sample_resampled_data, sample_config)
        with open(path) as f:
            payload = json.load(f)
        assert payload["metadata"]["total_points"] == len(sample_resampled_data.d)

    def test_metadata_has_timestamp(self, sample_resampled_data, sample_config, tmp_path, monkeypatch):
        monkeypatch.setattr("src.export.OUTPUT_DIR", tmp_path)
        path = export_json(sample_resampled_data, sample_config)
        with open(path) as f:
            payload = json.load(f)
        assert "generated_at" in payload["metadata"]

    def test_delta_range_present(self, sample_resampled_data, sample_config, tmp_path, monkeypatch):
        monkeypatch.setattr("src.export.OUTPUT_DIR", tmp_path)
        path = export_json(sample_resampled_data, sample_config)
        with open(path) as f:
            payload = json.load(f)
        assert "delta_range_s" in payload["metadata"]
        assert "min" in payload["metadata"]["delta_range_s"]
        assert "max" in payload["metadata"]["delta_range_s"]
