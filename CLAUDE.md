# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

Master's thesis research project measuring energy efficiency across 18 programming languages using the [Green Metrics Tool (GMT)](https://github.com/green-coding-solutions/green-metrics-tool). The 8 core benchmarks come from the [Computer Language Benchmarks Game](https://benchmarksgame-team.pages.debian.net/benchmarksgame/index.html).

## Key Commands

```bash
# Environment (Linux only)
make setup          # bootstrap full local env (Docker, GMT, Go, Python 3.12)
make uninstall      # teardown local env

# Running benchmarks
make measure                                        # all languages, all 8 benchmarks
make measure lang=go                                # single language
make measure lang=go,c bench=binary-trees,mandelbrot iterations=10
make measure lang=go profile=test                   # fast test run (--dev-no-sleeps, _test.yml files)

# Results pipeline
.venv/bin/python scripts/merge_results.py           # merge kwa/results/measurements_*.csv → results/results_linux.csv
# Then re-run notebooks/01_data_cleaning.ipynb to regenerate results_clean.csv + results_clean_runs.csv

# KWA exporter
make kwa-build      # compile to kwa/build/kwa
make kwa-run        # run from source

# KWA tests
cd kwa && GOCACHE=../.gocache_local go test ./...

# Notebooks (analysis/visualization)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter lab
```

## Languages & Paradigms

18 languages across 3 execution paradigms:

| Paradigm    | Languages |
|-------------|-----------|
| AOT         | C, C++, C#, Dart, Go, Haskell, Java, OCaml, Rust, Swift |
| JIT/VM      | Erlang, F#, JavaScript (Node.js), PHP, Ruby |
| Interpreted | Lua, Perl, Python |

> **Note on Java:** All Java benchmarks use **GraalVM Native Image** (AOT) via `ghcr.io/graalvm/native-image-community:23.0.2`. The community image only supports Serial GC — G1GC requires GraalVM Enterprise.
>
> **Note on F# and C#:** Benchmarks compile with `dotnet publish -c Release -r linux-x64 --self-contained true -p:PublishAot=true` using .NET 9 Native AOT. F# is classified as JIT because it targets the .NET runtime/CLR ecosystem despite AOT compilation here.

## Architecture

### Benchmark Layer (`benchmarks/<lang>/`)

Each language has one `.yml` file per benchmark for GMT to run. Naming conventions:
- `<benchmark>.yml` — canonical measurement run (`profile=measure`)
- `<benchmark>_test.yml` — fast smoke-test run (`profile=test`, uses smaller inputs)
- `gmt-cluster-scenario.yml` — all 8 benchmarks combined in separate flows (stdout suppressed to `/dev/null`); only present for `c` and `python`

Each YAML defines a `services` block (Docker container + optional `setup-commands` for compilation) and a `flow` block (sequence of timed commands). The C/C++/compiled language YMLs compile in `setup-commands`; interpreted languages just run directly in the flow.

`inputs/` holds shared input files (`fasta-*.txt`) mounted into containers at `/tmp/repo/inputs/`.

### `scripts/`

- **`measure.sh`** — orchestrates GMT runs; resolves which `benchmarks/<lang>/<bench>[_test].yml` files to pass to GMT's `runner.py` based on `lang=`, `bench=`, `profile=`, and `iterations=` arguments; calls `green-metrics-tool/runner.py` via the GMT venv Python directly
- **`merge_results.py`** — reads `kwa/results/measurements_*.csv` (one file per language), normalises container-specific disk/network column names (e.g. `node` → `container` for nodejs), concatenates all 18 files, and writes `results/results_linux.csv`
- **`setup.sh`** / **`uninstall.sh`** — called by `make setup` / `make uninstall`

### Results Pipeline

```
GMT runs → kwa export → kwa/results/measurements_<lang>.csv (18 files)
         → scripts/merge_results.py
         → results/results_linux.csv            (raw; 1440 rows, µJ/µs/µg/bytes/mW units)
         → notebooks/01_data_cleaning.ipynb
         → results/results_clean_runs.csv       (per-run, outliers removed, units converted)
         → results/results_clean.csv            (mean per language × benchmark)
```

**Outlier removal** (done in `01_data_cleaning.ipynb`): 1.5×IQR boxplot fence applied **per (language × benchmark)** group on CPU energy + execution time; IQR=0 groups are skipped. Minimum 5 clean runs per cell enforced.

**Unit conversions**: µJ → J (÷1e6), µs → ms (÷1e3), µg → g (÷1e6), Bytes → MB (÷1e6), mW → W (÷1e3).

### KWA (`kwa/`)

Go CLI that reads measurements out of GMT's Postgres DB and exports them to CSV. Layer dependency chain:

```
cli → app/export + app/measure → api → service → data
```

- **`cmd/main.go`** — entrypoint
- **`internal/cli/`** — Cobra commands + Bubble Tea TUI (model/update/view split across `tui_model.go`, `tui_update.go`, `tui_view.go`)
- **`internal/app/export/`** — request contract, timestamp parsing/validation, executor orchestration
- **`internal/app/measure/`** — measure workflow executor (runs `scripts/measure.sh`, captures timestamps, then auto-exports)
- **`internal/service/`** — CSV serialization pipeline; parser maps metric keys to columns
- **`internal/data/`** — SQL queries against GMT's `phase_stats` table
- **`internal/constant/catalog.go`** — canonical lists of languages and benchmarks (used by both TUI multi-select and validation)

The CSV schema has fixed columns `run_id, measured_at, language, benchmark` followed by dynamic metric columns discovered from the data.

See `kwa/CLAUDE.md` for detailed kwa-specific guidance.

### `notebooks/`

Jupyter notebooks for data analysis.

**v1 (original):**
- `01_data_cleaning.ipynb` — upstream cleaning pipeline; the single source of truth for outlier removal and unit conversion; exports `results_clean.csv` (aggregated) and `results_clean_runs.csv` (per-run)
- `02_visualization.ipynb` — cross-language ranking and thesis-ready charts; loads `results_clean.csv`
- `03–10` — per-benchmark deep dives (binary-trees, fannkuch-redux, fasta, k-nucleotide, mandelbrot, n-body, regex-redux, spectral-norm)
- `11_disk_io_deep_dive.ipynb` — disk I/O analysis

**v2 (`notebooks/v2/`):**
Generated by `notebooks/v2/generate_notebooks.py` (run the script to regenerate all 4 notebooks). All v2 notebooks load from `results/results_clean_runs.csv` — no inline outlier removal.

- `01_data_profiling_v2.ipynb` — EDA: column overview, missing values, distributions, data coverage heatmap, per-language summary
- `02_energy_analysis_v2.ipynb` — CPU + memory energy boxplots, paradigm violin plots, Kruskal-Wallis + Mann-Whitney U + Bonferroni + rank-biserial, per-benchmark heatmap, efficiency ranking
- `03_time_analysis_v2.ipynb` — execution time boxplots (log scale), Spearman correlations, paradigm speed comparison, EDP ranking
- `04_comparative_v2.ipynb` — normalized ranking table (ratio vs best language), multi-metric ranking (mean of benchmark means, sorted by EDP rank), radar chart, normalised heatmap, top3/bottom3, key findings; exports `outputs/ranking_summary.csv`

**v2 key conventions:**
- Figures saved to `notebooks/v2/figures/` (gitignored)
- Outputs (CSVs) saved to `notebooks/v2/outputs/` (gitignored)
- EDP = (CPU Energy + Memory Energy) × Time (J·ms), computed per cell from `results_clean.csv` mean values
- Rankings, heatmaps and summary tables use the two-step mean: per-(language × benchmark) mean → per-language mean (equal benchmark weight), sourced from `results_clean.csv`. Boxplots/violins remain distribution views (median visible, ordered by mean, mean marked); paradigm significance keeps the non-parametric Kruskal-Wallis / Mann-Whitney tests on the per-run data

### `docs/`

- `docs/flags.md` — compiler flags and build settings for all 18 languages across all 8 benchmarks; derived from CLBG reference implementations
- `docs/benchmarks/benchmark-analysis.md` — thesis benchmark analysis plan and methodology
- `docs/benchmarks/<lang>_benchmark_insights.md` — per-language CLBG implementation notes (18 files)
- `docs/clbg-prompt-template.md` — prompt template for reviewing CLBG implementations
- `docs/credits.md` — attribution for CLBG source code

### `green-metrics-tool/`

GMT subproject cloned locally by `make setup`. Not committed to this repo — generated on setup. The GMT venv at `green-metrics-tool/venv/` is used directly by `scripts/measure.sh`.

## Benchmark YAML Structure

```yaml
services:
  <container-name>:
    image: <docker-image>
    setup-commands:           # optional — for compilation
      - command: gcc ... -o /tmp/<binary>
    command: sleep infinity   # keep container alive

flow:
  - name: <Flow-Name>
    container: <container-name>
    commands:
      - type: console
        shell: sh             # required when using shell redirects (< or >)
        command: <cmd>
```

In `gmt-cluster-scenario.yml` files, each of the 8 benchmarks is a separate flow entry within the same service, all with `> /dev/null` to suppress stdout.

## Conventions

- Default to non-destructive operations; do not reset/revert unrelated changes.
- Validate behavior with focused tests first, then broader suites when touching shared paths.
- Keep docs and README pointers aligned when contracts or UX behavior change.
- Do not add `Co-Authored-By: Claude` or any Claude co-author line to commit messages.

## Commenting Standard

Every new or modified function must have a leading comment covering: behavior, key inputs, outputs/return value, notable side effects and errors. Keep comments concise and factual.
