# Results Pipeline

> Part of the [main README](../README.md).

```
GMT runs → kwa export → kwa/results/measurements_<lang>.csv   (one file per language)
         → scripts/merge_results.py
         → results/results_linux.csv          (raw; µJ / µs / µg / bytes / mW)
         → notebooks/01_data_cleaning.ipynb   (outlier removal + unit conversion)
         → results/results_clean_runs.csv     (per-run, outliers removed)
```

Outliers are removed per (language × benchmark) group using a 1.5×IQR fence on CPU energy
and execution time; units are converted to J / s / g / MB / W.

## Results

> _To be completed._

Cleaned data lives in `results/results_clean_runs.csv` (per run). Per-(language × benchmark)
means are derived inline in the notebooks (`plot_style.cell_means`). Analysis and figures are
produced by the notebooks in `notebooks/` (see `notebooks/v2/`). A summary of findings will go
here.
