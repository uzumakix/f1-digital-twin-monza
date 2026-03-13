# f1-digital-twin-monza

Spatial telemetry reconstruction for F1 qualifying. Converts time-series sensor data into a distance-domain delta map that shows where each driver gains or loses, metre by metre.

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776ab?style=flat-square&logo=python&logoColor=white)
![License MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![CI](https://img.shields.io/github/actions/workflow/status/uzumakix/f1-digital-twin-monza/ci.yml?style=flat-square&label=tests)

## example output

VER vs SAI, 2023 Monza Qualifying:

![telemetry chart](results/telemetry_analysis.png)

Top panel: speed traces for both drivers. Bottom panel: cumulative time delta. Blue fill = VER ahead, green fill = SAI ahead. The delta oscillates because the two cars have different strengths at different parts of the track.

![delta detail](results/delta_detail.png)

Corner annotations show where each driver gains. SAI recovers time in the chicane braking zones (Roggia, Ascari). VER builds his gap through the Lesmo complex where the RB19's downforce pays off at high cornering speeds.

Full analysis with driver technique breakdown: [docs/analysis.md](docs/analysis.md)

## how it works

```
raw telemetry (time-indexed)
    --> piecewise-linear interpolation
    --> resample onto shared 1m distance grid
    --> compute dt(d) = t_A(d) - t_B(d) at every metre
    --> render chart with corner markers
```

1. Load session via FastF1 (caches locally after first download)
2. Extract fastest lap telemetry for both drivers
3. Build interpolators: distance to elapsed time and speed
4. Evaluate on a common 1-metre grid
5. Plot speed traces and cumulative delta

Negative delta = driver A ahead. Final value converges to the official qualifying gap.

## usage

```bash
git clone https://github.com/uzumakix/f1-digital-twin-monza.git
cd f1-digital-twin-monza
pip install -r requirements.txt
python main.py
```

First run downloads ~50-80 MB of session data from FIA. Cached runs take 3-5 seconds.

```bash
python main.py                                 # default: VER vs SAI, Monza 2023 Q
python main.py --config configs/spa_2023.yaml  # different session
python main.py --export csv                    # export resampled data
python main.py --export both --no-chart        # data only
```

## configuration

Session parameters live in YAML files. No code changes needed to switch drivers or circuits.

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

## project structure

```
src/
    ingest.py       session loading via FastF1
    resample.py     time-to-distance domain transform (scipy interp1d)
    visualise.py    two-panel chart renderer
    config.py       typed dataclass config + YAML loader
    export.py       CSV and JSON data export
configs/            YAML session definitions
tests/              unit tests with synthetic telemetry fixtures
docs/               race analysis writeups
```

## tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Tests use synthetic telemetry (no network needed). Covers interpolator correctness, grid bounds, delta sign, array alignment, export formats, and config loading.

## limitations

- Resolution caps at ~240 Hz (FastF1 interpolation limit)
- No tyre compound correction
- Track evolution across the session is not modelled
- Corner positions are approximate (manually measured from track maps)
- Fuel load differences between laps are ignored

## tech

FastF1 for telemetry ingestion, scipy for piecewise linear interpolation, numpy for grid construction, pandas for timedelta handling, matplotlib for charting.

## license

[MIT](LICENSE)
