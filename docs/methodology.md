# Signal Processing Methodology

## Data Source

Telemetry comes from the FIA timing system, accessed through the FastF1 Python API. Each lap provides time-series channels at approximately 240 Hz: speed (km/h), throttle (%), brake (binary), RPM, gear, and GPS-derived distance from the start/finish line. The data is session-specific. We pull individual laps from qualifying or race sessions and work with them independently.

FastF1 handles the initial data retrieval and caching. We do not apply any of its built-in interpolation or correction features beyond the default distance calculation, since we want to control the signal processing pipeline ourselves.

## Numerical Differentiation

Acceleration is not directly available in the telemetry. We compute it from the speed channel using `np.gradient`, which applies second-order central differences:

```
a[i] = (v[i+1] - v[i-1]) / (t[i+1] - t[i-1])
```

At the boundaries it falls back to first-order forward/backward differences. We chose central differences over forward differences because forward differencing (`(v[i+1] - v[i]) / dt`) shifts the signal by half a sample and amplifies high-frequency noise more aggressively. The central scheme has O(dt^2) error vs O(dt) for forward.

We did not use Savitzky-Golay filtering at the differentiation stage. SG fits a local polynomial and differentiates analytically, which gives a smoother derivative, but it also smears sharp transients. Since we specifically need to detect the onset of braking (a sharp deceleration event), we preferred the raw noisy derivative and handled smoothing separately.

Speed is converted from km/h to m/s before differentiation (divide by 3.6). The resulting acceleration is in m/s^2. For display and threshold comparisons we convert to G by dividing by 9.81.

## Smoothing

For visualization purposes only, we smooth the acceleration signal with `scipy.ndimage.uniform_filter1d` using a window of 5 samples. At 240 Hz this corresponds to roughly 21 ms, which removes per-sample jitter without distorting the overall deceleration profile. The smoothed signal is used in plots. All detection logic operates on the unsmoothed signal.

## Braking Zone Isolation

We isolate the braking zone for Turn 1 (Rettifilo chicane) by spatial windowing: only data points where the car is between 600 m and 1050 m from the start/finish line are considered. These bounds were chosen by inspecting the Monza track map and picking a region that starts well before the earliest possible braking point and ends after the corner apex. This avoids false detections from other parts of the lap.

## Brake Point Detection

Within the spatial window, we scan the acceleration signal for the first sample where deceleration exceeds 0.5 G (i.e., acceleration < -4.905 m/s^2). That sample's distance and time values are recorded as the brake point.

The 0.5 G threshold was chosen empirically. Normal coasting and aero drag produce decelerations up to about 0.2-0.3 G. Initial brake application causes a rapid jump past 0.5 G within one or two samples. A lower threshold would trigger on lift-and-coast phases; a higher one would miss gentle initial brake applications in some laps.

## Validation

We validated the computed brake points against the binary brake channel in the telemetry. The brake channel transitions from 0 to 1 when the driver presses the brake pedal. For the laps we tested, the computed threshold crossing aligned with the brake channel transition within 8 ms, which is about 2 samples at 240 Hz. This is within the expected uncertainty given that the brake channel itself has finite resolution and may not capture the exact instant of pad contact.

## Error Sources

**GPS distance uncertainty.** The distance-from-start values are derived from GPS coordinates. Typical GPS accuracy on a well-mapped circuit is around 1 m, which at 300 km/h corresponds to about 12 ms of temporal uncertainty. This dominates the spatial accuracy of brake point locations.

**Differentiation noise.** Numerical differentiation is a high-pass operation. Any measurement noise in the speed channel gets amplified, especially at higher frequencies. At 240 Hz with speed quantized to 0.1 km/h resolution, the differentiation noise floor is roughly 0.3 m/s^2 (about 0.03 G). This is below our detection threshold but visible in raw acceleration plots.

**Sampling jitter.** The telemetry is nominally 240 Hz but not perfectly uniform. Sample intervals vary by up to 0.5 ms around the nominal 4.17 ms. We use actual timestamps for differentiation rather than assuming uniform spacing, which handles this correctly at the cost of slightly uneven frequency content in the derivative.

## Units

| Quantity | Raw unit | Converted unit |
|----------|----------|----------------|
| Speed | km/h | m/s (divide by 3.6) |
| Acceleration | m/s^2 | G (divide by 9.81) |
| Time | seconds | seconds |
| Distance | meters | meters |
| Sampling rate | ~240 Hz | ~4.17 ms per sample |
