import pytest
import numpy as np
import pandas as pd

@pytest.fixture
def sample_telemetry():
    # synthetic telemetry: 100 points, 300->100 km/h linear decel over 2 seconds
    n = 100
    t = np.linspace(0, 2, n)
    speed = np.linspace(300, 100, n)
    distance = np.cumsum(speed * (1000/3600) * (2/n))
    distance += 600  # start at T1 entry
    df = pd.DataFrame({
        'Speed': speed,
        'Distance': distance,
        'SessionTime': pd.to_timedelta(t, unit='s'),
    })
    return df
