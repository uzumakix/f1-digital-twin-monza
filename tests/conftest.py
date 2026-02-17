import numpy as np
import pandas as pd
import pytest
from src.config import Config
from src.resample import ResampledData

@pytest.fixture
def mock_telemetry():
    def _make(n_points=100, max_dist=5000.0, lap_time=70.0):
        d = np.linspace(0, max_dist, n_points)
        t = pd.to_timedelta(np.linspace(0, lap_time, n_points), unit='s')
        v = 200 + 50 * np.sin(d / max_dist * 4 * np.pi)
        return pd.DataFrame({'Distance': d, 'Time': t, 'Speed': v})
    return _make

@pytest.fixture
def sample_resampled_data():
    n = 100
    return ResampledData(
        d=np.linspace(0, 5000, n),
        t_a=np.linspace(0, 70, n),
        t_b=np.linspace(0, 70.1, n),
        v_a=np.full(n, 300.0),
        v_b=np.full(n, 298.0),
        delta=np.linspace(0, -0.1, n),
    )

@pytest.fixture
def sample_config():
    return Config()
