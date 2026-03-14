# f1-digital-twin-monza

Kinematic trajectory comparison between Verstappen and Sainz during 2023 Monza Qualifying. Uses FIA telemetry resampled onto a uniform 1-metre distance grid to isolate where time is gained and lost across 5.793 km of circuit.

## What the project finds

![track delta](results/track_delta.png)

The 0.013s pole gap between SAI (1:20.294) and VER (1:20.307) is the residual of much larger opposing swings. SAI gains ~0.05–0.08s total in braking zones (T1 Grande, Roggia, Ascari) by committing to brake points ~10m later at 340 km/h approach speeds. VER recovers a similar margin through medium-speed corners (Lesmos) where higher aerodynamic load permits 3–5 km/h more apex speed.

![telemetry](results/telemetry_analysis.png)

The cumulative time delta (bottom panel) shows these gains trading back and forth until settling at +0.019s by the finish line. A lap-time comparison alone would hide this structure entirely.

## How it works

Telemetry from the FIA is time-indexed, but comparing two laps in the time domain is meaningless because the drivers occupy different positions at the same timestamp. The pipeline converts both laps to the distance domain:

1. For each driver, build a piecewise-linear interpolator mapping distance → elapsed time and distance → speed (via `scipy.interpolate.interp1d`).
2. Evaluate both interpolators on a shared distance grid with 1 m spacing.
3. Compute the time delta at each grid point: `Δt(d) = t_ref(d) − t_cmp(d)`.

This is a standard spatial resampling approach used in traffic flow analysis and vehicle kinematics — the same principle behind the Intelligent Driver Model's position-based formulation, applied here to single-lap telemetry rather than car-following scenarios.

## Project structure

```
src/
    ingest.py       load session + extract laps (FastF1 API)
    resample.py     time-to-distance resampling (scipy interp1d)
    visualise.py    two-panel speed + delta chart
    config.py       YAML config loader with dataclass validation
    export.py       CSV/JSON telemetry export
configs/
    monza_2023.yaml VER vs SAI qualifying config
    spa_2023.yaml   VER vs LEC qualifying config
tests/              25 unit tests, synthetic fixtures, no network needed
results/            generated plots
```

### Setup

```bash
git clone https://github.com/uzumakix/f1-digital-twin-monza.git
cd f1-digital-twin-monza
pip install -r requirements.txt
python main.py
```

First run downloads ~50 MB of FIA data (cached locally after that). Switch sessions:

```bash
python main.py --config configs/spa_2023.yaml
python main.py --export csv
```

## References

- Treiber, M., Hennecke, A., & Helbing, D. (2000). *Congested traffic states in empirical observations and microscopic simulations.* Physical Review E, 62(2), 1805–1824. — Foundational position-based kinematic model for vehicle trajectory analysis.
- Bando, M., Hasebe, K., Nakayama, A., Shibata, A., & Sugiyama, Y. (1995). *Dynamical model of traffic congestion and numerical simulation.* Physical Review E, 51(2), 1035–1042. — Optimal velocity model; distance-domain formulation of vehicle dynamics.
- Kesting, A., Treiber, M., & Helbing, D. (2010). *Enhanced intelligent driver model to access the impact of driving strategies on traffic capacity.* Philosophical Transactions of the Royal Society A, 368(1928), 4585–4605. — Extended kinematic model with lane-change and acceleration profiles.
- FastF1 documentation and FIA telemetry data format: [theOehrly/Fast-F1](https://github.com/theOehrly/Fast-F1).

[MIT](LICENSE)
