[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-purple.svg)](https://github.com/astral-sh/ruff)

# f1-digital-twin-monza

Spatial telemetry reconstruction for the 2023 Italian GP Qualifying. Converts raw time-series sensor data into a distance-domain performance map that shows where each driver gains or loses, metre by metre.

Built for VER vs SAI. Configurable for any driver pairing or session via YAML.



## Why this exists

A lap time is one number. It collapses 4.7 km of complex spatial performance into a single figure and hides everything interesting.

This tool reverses that collapse. It reconstructs where the time lives on track, exposing the mechanical and human story underneath the headline gap. For 2023 Monza, it reveals Ferrari's braking zone advantage and Red Bull's cornering efficiency nearly cancelling each other. The 0.066s gap is the residual of much larger gains in opposite directions.

Full race analysis with driver technique breakdown: [docs/analysis.md](docs/analysis.md)

## How it works

```
Raw telemetry (time-indexed)  -->  Spatial resampling (1m grid)  -->  Delta computation  -->  Chart
```

1. Load qualifying session via FastF1 (cached locally after first run)
2. Extract fastest lap telemetry for both drivers
3. Build piecewise-linear interpolators: distance to elapsed time and speed
4. Evaluate both on a shared 1-metre grid
5. Compute `dt(d) = t_A(d) - t_B(d)` at every grid point
6. Render two-panel chart with corner annotations

Negative delta = driver A ahead. Positive = driver B ahead. Final value converges to the official gap.

## Quick start

```bash
git clone https://github.com/<your-username>/f1-digital-twin-monza.git
cd f1-digital-twin-monza

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python main.py
```

First run downloads ~50-80 MB of session data. Cached runs take 3-5 seconds.

## Usage

```bash
python main.py                              # Default: VER vs SAI, Monza 2023 Q
python main.py --config configs/spa.yaml    # Different session
python main.py --export csv                 # Export resampled data
python main.py --export both --no-chart     # Data only, skip chart
```

## Configuration

Session parameters live in YAML. No code changes needed.

```yaml
# configs/monza_2023.yaml
session:
  year: 2023
  circuit: Monza
  type: Q

drivers:
  reference: VER
  comparison: SAI

grid:
  step_metres: 1

corners:
  - ["T1 Grande", 295]
  - ["Roggia", 680]
  - ["Lesmo 1", 1430]
  - ["Lesmo 2", 1650]
  - ["Ascari", 3450]
  - ["Parabolica", 4400]
```

## Project structure

```
src/
    config.py       Typed configuration with dataclass validation
    ingest.py       Session loading and lap extraction
    resample.py     Time-to-distance domain transformation
    visualise.py    Chart rendering with configurable theme and corners
    export.py       CSV and JSON data export
configs/            YAML session definitions and corner maps
tests/              Unit tests with synthetic telemetry fixtures
docs/               Race analysis and methodology
```

## Development

```bash
make test       # pytest suite
make lint       # ruff check + format
make run        # Run analysis
make export     # CSV + JSON output
make clean      # Remove cache and outputs
```

## Tech stack

| Library | Role |
|---|---|
| **fastf1** | Telemetry ingestion via FIA live timing |
| **scipy** | Piecewise linear interpolation for domain resampling |
| **numpy** | Vectorised grid construction and delta arithmetic |
| **pandas** | Dataframe manipulation and timedelta handling |
| **matplotlib** | Dark-mode publication-quality charts |
| **pyyaml** | Configuration management |

## Limitations

Resolution caps at ~240 Hz (FastF1 interpolation). No tyre compound correction. Track evolution across the session is not modelled. Corner positions are approximate.

## License

[MIT](LICENSE)

