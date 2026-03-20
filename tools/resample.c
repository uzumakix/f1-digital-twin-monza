/*
 * resample.c -- Linear interpolation resampler for time series CSV
 *
 * Reads two-column CSV (time, value) from stdin, outputs uniformly
 * spaced samples to stdout using linear interpolation.
 *
 * Usage:
 *   ./resample --dt 0.004 < telemetry.csv > resampled.csv
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_LINE 256
#define MAX_SAMPLES 500000

static double times[MAX_SAMPLES];
static double values[MAX_SAMPLES];

static double lerp(double t, double t0, double t1, double v0, double v1) {
    double alpha = (t - t0) / (t1 - t0);
    return v0 + alpha * (v1 - v0);
}

static void usage(const char *prog) {
    fprintf(stderr, "Usage: %s --dt <interval>\n", prog);
    fprintf(stderr, "Reads CSV (time,value) from stdin, writes resampled CSV to stdout.\n");
    exit(1);
}

int main(int argc, char *argv[]) {
    double dt = 0.0;
    int i;

    /* parse args */
    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--dt") == 0 && i + 1 < argc) {
            dt = atof(argv[++i]);
        } else {
            usage(argv[0]);
        }
    }

    if (dt <= 0.0) {
        fprintf(stderr, "Error: --dt must be positive\n");
        usage(argv[0]);
    }

    /* read input, skip header */
    char line[MAX_LINE];
    int n = 0;

    if (fgets(line, MAX_LINE, stdin) == NULL) {
        fprintf(stderr, "Error: empty input\n");
        return 1;
    }

    while (fgets(line, MAX_LINE, stdin) != NULL) {
        if (n >= MAX_SAMPLES) {
            fprintf(stderr, "Error: exceeded %d samples\n", MAX_SAMPLES);
            return 1;
        }
        if (sscanf(line, "%lf,%lf", &times[n], &values[n]) == 2) {
            n++;
        }
        /* skip malformed lines silently */
    }

    if (n < 2) {
        fprintf(stderr, "Error: need at least 2 data points, got %d\n", n);
        return 1;
    }

    /* resample */
    double t_start = times[0];
    double t_end = times[n - 1];
    int j = 0; /* index into input */

    printf("time,value\n");

    double t = t_start;
    while (t <= t_end) {
        /* advance j so that times[j] <= t < times[j+1] */
        while (j < n - 2 && times[j + 1] < t) {
            j++;
        }

        double v = lerp(t, times[j], times[j + 1], values[j], values[j + 1]);
        printf("%.6f,%.6f\n", t, v);

        t += dt;
    }

    return 0;
}
