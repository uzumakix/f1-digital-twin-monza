import pytest
from src.config import Config, load_config

class TestConfigDefaults:
    def test_default_session(self):
        cfg = Config()
        assert cfg.session.year == 2023
        assert cfg.session.circuit == 'Monza'

    def test_default_drivers(self):
        cfg = Config()
        assert cfg.drivers.reference == 'VER'
        assert cfg.drivers.comparison == 'SAI'

    def test_default_corners_not_empty(self):
        cfg = Config()
        assert len(cfg.corners) > 0

class TestLoadConfig:
    def test_missing_file_returns_defaults(self, tmp_path):
        cfg = load_config(str(tmp_path / 'nonexistent.yaml'))
        assert cfg.session.year == 2023

    def test_partial_override(self, tmp_path):
        f = tmp_path / 'test.yaml'
        f.write_text('session:\n  year: 2024\n  circuit: Spa\n  type: Q\n')
        cfg = load_config(str(f))
        assert cfg.session.year == 2024
        assert cfg.drivers.reference == 'VER'
