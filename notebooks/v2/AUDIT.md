# Notebook Audit — Phase 0

> **Status: COMPLETE.** Cut-list approved (§5) and applied. Phase 1 (plot_style),
> Phase 2 (per-notebook refactor) and Phase 3 (verify) are done — see §7 for the
> Phase 3 verification report.

Scope (confirmed): **all 7 notebooks** —
`01_data_cleaning`, `02_visualization`, `11_disk_io_deep_dive` (v1, in `notebooks/`)
and `v2/01`–`v2/04`.

Reminder: the four `v2/*.ipynb` are **generated** by
[`generate_notebooks.py`](generate_notebooks.py). Any v2 edit is really an edit to
that generator, then a regenerate. v1 notebooks are hand-edited directly.

---

## 1. Cross-cutting findings (the consistency problems Phase 1 must fix)

### 1a. Three different paradigm colour palettes, none colourblind-safe
| Source | AOT | JIT/VM | Interpreted |
|--------|-----|--------|-------------|
| `v2/*` (`PARADIGM_COLORS`) | `#2980b9` | `#e67e22` | `#27ae60` |
| `v1/02` ranking-table tiers | `#d6eaf8` | `#fdebd0` | `#fdedec` (pastel) |
| `v1/11` startup-overhead tiers | `#4c9be8` | `#f5a623` | `#e85454` |
| **Plan target (Okabe–Ito)** | `#0072B2` | `#E69F00` | `#009E73` |

→ Phase 1 collapses all of these to the single Okabe–Ito set in `plot_style.py`.

### 1b. Paradigm **membership** disagrees between notebooks (a real bug, not just colour)
- Canonical (CLAUDE.md, `v2/*`, `v1/02`): JIT = {Erlang, F#, JavaScript, PHP, Ruby};
  Interpreted = {Lua, Perl, Python}.
- **`v1/11` cell[22]** uses JIT = {Erlang, JavaScript, Ruby, PHP, **Lua**};
  Interpreted = {**Python, Perl** only}. → **Lua is mis-grouped as JIT** and F# is
  absent. This silently mislabels the only colour-coded figure in nb11.

### 1c. Figure export format is inconsistent
- `v2/*` save **`.png` @ 150 dpi** (raster) — violates the DoD (300-dpi vector PDF).
- `v1/02`, `v1/11` save **`.pdf` @ 300 dpi** to `results/figs/` (not `figures/`).
- `figures/` and `outputs/` are gitignored (per CLAUDE.md) — fine, but note thesis
  PDFs won't be version-controlled unless we change that.

### 1d. rcParams / style set three different ways
- `v2/*`: `sns.set_theme("whitegrid")` + dpi 150, no font family.
- `v1/02`, `v1/11`: serif font, dpi 150/300, manual `rcParams`.
- No shared module — every notebook redefines `LANG_DISPLAY` and (v2) the full
  `PARADIGM` / `PARADIGM_COLORS` / `MEANPROPS` block inline.

### 1e. Heavy figure duplication v1 ↔ v2 (see matrix §2)
`v1/02_visualization` is **almost entirely superseded** by `v2/02`+`v2/03`+`v2/04`:
every chart it produces has a newer two-step-mean equivalent in v2. Strong candidate
to retire the notebook (or strip it to whatever is genuinely unique).

### 1f. `figures/` naming is ad-hoc
Names like `cpu_energy_by_language.png`, `total_energy_stacked.png` are reasonable but
not prefixed/numbered. Phase 1 `save_fig()` should impose a consistent scheme
(e.g. `02_cpu_energy_ranking.pdf`).

---

## 2. Duplicate-figure matrix (same data, shown more than once)

| Figure / claim | v1 location | v2 location | Proposal |
|---|---|---|---|
| CPU-energy ranking (bar) | `02` cell[10],[18] | `02` cell[19] | keep v2 (two-step mean, paradigm-coloured); CUT v1 |
| Per-benchmark CPU/mem energy heatmap | `02` cell[8] | `02` cell[16] | keep v2; CUT v1 |
| Per-benchmark **time** heatmap | `02` cell[8] | `03` cell[15] | keep v2; CUT v1 |
| Energy-vs-time scatter | `02` cell[12] | `03` cell[7] | keep v2; CUT v1 |
| Normalised ranking table | `02` cell[17],[18] | `04` cell[7] | keep v2; CUT v1 |
| Per-benchmark grid bars (energy/time/carbon) | `02` cell[16] | — (only v1) | DECIDE: unique to v1 |
| Stacked CPU+mem energy | `02` cell[14] | `02` cell[10] | keep v2; CUT v1 |
| Disk-read heatmap / grids / strips / scatter | `11` cells[5,7,11,13,15] | — | per plan hint: CUT (see §4) |

---

## 3. Per-notebook cell tables

### `notebooks/01_data_cleaning.ipynb` (pipeline; produces `results_clean_runs.csv`)
| # | type | produces | question it answers | KEEP/MERGE/CUT | reason |
|---|------|----------|---------------------|----------------|--------|
| 0 | md | title | — | KEEP | |
| 1 | code | imports + paths | — | KEEP | |
| 2 | md | "Load raw" | — | KEEP | |
| 3 | code | load raw df | — | KEEP | |
| 4 | md | outlier method | methodology | KEEP | |
| 5 | code | outlier mask + `df_clean` (no fig; `boxplot` is a fn name) | how many runs dropped | KEEP | core pipeline |
| 6 | code+fig | CPU-energy boxplots per benchmark, outliers in red | "is the 1.5×IQR fence sane?" | **KEEP (methodology fig)** | good appendix figure justifying cleaning |
| 7 | code | <5-runs-per-cell guard (print+table) | data-quality gate | KEEP | QA gate, no fig |
| 8 | code+fig | bar: clean-run counts per group | internal QA | **CUT?** | duplicates cell[7]'s table; low thesis value |
| 9 | md | "Unit conversions" | — | KEEP | |
| 10 | code | unit conversion | — | KEEP | core pipeline |
| 11 | md | "Export" | — | KEEP | |
| 12 | code | write CSV | — | KEEP | |

### `notebooks/02_visualization.ipynb` (v1)
| # | type | produces | question | KEEP/MERGE/CUT | reason |
|---|------|----------|----------|----------------|--------|
| 0 | md | title ("loads results_clean.csv") | — | MERGE | stale text (file removed); rewrite or drop with notebook |
| 1 | code | imports + serif style | — | MERGE→`plot_style` | |
| 2 | code | load + inline mean + `LANG_DISPLAY` | — | KEEP/MERGE | |
| 3 | code | print metric cols | scratch | **CUT** | exploratory print |
| 4 | md | "helper" | — | CUT-with | |
| 5 | code | `pivot()`,`save()` helpers | — | MERGE→`plot_style` | |
| 6 | md | "Heatmaps" | — | — | |
| 7 | code | `find_col` + COL defs | — | MERGE→`plot_style` | |
| 8 | code+fig×3 | heatmaps: CPU energy / time / CPU carbon | per-cell intensity | **CUT** | dup of v2/02 c16 & v2/03 c15 |
| 9–10 | md+fig×3 | ranked bars: CPU energy / carbon / time | language ranking | **CUT** | dup of v2 rankings |
| 11–12 | md+fig | energy-vs-time scatter | efficiency quadrant | **CUT** | dup of v2/03 c7 |
| 13–14 | md+fig | stacked CPU+mem energy | energy split | **CUT** | dup of v2/02 c10 |
| 15–16 | md+fig×4 | **per-benchmark grid bars** (energy/time/mem/carbon) | per-benchmark ranking | **DECIDE** | only-in-v1; small-multiple ranking. Keep (move to v2) or cut? |
| 17 | code | normalised ranking agg | — | CUT | feeds c18 |
| 18 | code+fig | normalised ranking **table** (tiered colours) | overall ranking | **CUT** | dup of v2/04 c7 + uses pastel palette |

> Net proposal for `v1/02`: **retire the notebook**, optionally salvaging only the
> per-benchmark grid-bars (cell 16) into a v2 notebook if you want that view. Your call.

### `notebooks/11_disk_io_deep_dive.ipynb` (v1)
Plan hint: *"only Runtime startup disk overhead is expected to survive."*
| # | type | produces | question | KEEP/MERGE/CUT | reason |
|---|------|----------|----------|----------------|--------|
| 0 | md | title/findings | — | MERGE | keep trimmed intro |
| 1 | code | imports/style/helpers | — | MERGE→`plot_style` | |
| 2–3 | md+code | load runs+means | — | KEEP | |
| 4–5 | md+fig×2 | disk read/write heatmaps | I/O per cell | **CUT?** | exploratory; disk I/O is minor to thesis |
| 6–7 | md+fig×2 | grid bars read/write per benchmark | per-benchmark I/O | **CUT?** | exploratory |
| 8–9 | md+code | I/O-benchmark setup table | — | CUT-with | |
| 10–11 | md+fig | strip plots per-run reads | run consistency | **CUT?** | QA-ish |
| 12–13 | md+fig | ranked bars reads (knuc/regex) | which lang reads most | **CUT?** | |
| 14–15 | md+fig | reads-vs-time scatter | does I/O slow runs? | **CUT?** | |
| 16–17 | md+fig | disk writes (all) | writes negligible | **CUT?** | confirms a non-finding |
| 18–20 | md+code+fig | summary table reads/writes | — | **CUT?** | |
| 21 | md | startup overhead intro | — | KEEP | |
| 22 | code+fig | **runtime startup disk overhead per language** | runtime load cost | **KEEP** ⭐ | the surviving figure; **fix paradigm mis-grouping (§1b) + palette** |

> Net proposal for `v1/11`: collapse to load + the single startup-overhead figure
> (with corrected paradigm grouping). Everything else CUT pending your confirmation.

### `notebooks/v2/01_data_profiling_v2.ipynb`
| # | type | produces | question | KEEP/MERGE/CUT | reason |
|---|------|----------|----------|----------------|--------|
| 0 | md | purpose | — | KEEP | already has purpose line |
| 1–2 | code | imports + constants + load | — | MERGE→`plot_style` | |
| 3–4 | md+code | describe table (+median/IQR/skew) | distribution shape | KEEP | EDA, evidences skew |
| 5–6 | md+code | missing-value / zero-fraction check | data completeness | KEEP | QA, no fig |
| 7–8 | md+fig | log₁₀ histograms ×3 (cpu/mem/time) | skewness | KEEP | justifies non-parametric tests |
| 9–10 | md+fig | coverage heatmap (runs/cell) | balanced coverage? | KEEP | methodology |
| 11–12 | md+code | per-language summary table (mean+median) | overview | KEEP | EDA table |

> nb01 is healthy. Main change: import shared style, switch any saved fig to PDF.

### `notebooks/v2/02_energy_analysis_v2.ipynb` ⭐ (core)
| # | type | produces | question | KEEP/MERGE/CUT | reason |
|---|------|----------|----------|----------------|--------|
| 0 | md | purpose/methodology | — | MERGE | fix stale "results_clean.csv" ref |
| 1–2 | code | imports+constants+load | — | MERGE→`plot_style` | |
| 3–4 | md+fig | CPU energy boxplot, all langs, sorted by mean | most efficient? | KEEP | |
| 5 | fig | CPU energy boxplots split per paradigm | within-paradigm spread | KEEP/**DECIDE** | possibly redundant w/ cell4 |
| 6–7 | md+fig | Memory energy boxplot, all langs | mem ranking | KEEP | |
| 8 | fig | Memory energy per-paradigm split | spread | KEEP/**DECIDE** | same redundancy Q as cell5 |
| 9–10 | md+fig | stacked total energy | CPU vs mem share | KEEP | |
| 11 | fig | CPU-vs-mem scatter | which dominates | KEEP | |
| 12–13 | md+fig | energy violins by paradigm | paradigm distribution | KEEP | |
| 14 | code | KW + MWU + rank-biserial prints | significance | KEEP | stats (no fig) |
| 15–16 | md+fig | per-benchmark CPU+mem heatmap | per-cell intensity | KEEP | |
| 17–18 | md+code | efficiency ranking table | ranking | KEEP | |
| 19 | fig | CPU energy ranking barh | ranking | KEEP | |
| 20–21 | md+fig | **CO₂ carbon correlation scatter** | energy↔carbon | **CUT?** | carbon = energy × constant ⇒ r≈1.0 by construction; adds little. Keep one line of text instead? |

### `notebooks/v2/03_time_analysis_v2.ipynb`
| # | type | produces | question | KEEP/MERGE/CUT | reason |
|---|------|----------|----------|----------------|--------|
| 0 | md | purpose | — | MERGE | fix stale csv ref |
| 1–2 | code | setup | — | MERGE→`plot_style` | |
| 3–4 | md+fig | time boxplot all langs (log) | fastest? | KEEP | |
| 5 | fig | time boxplots per paradigm (log) | spread | KEEP/**DECIDE** | redundancy Q |
| 6–7 | md+fig | time-vs-CPU-energy scatter (Spearman) | correlation | KEEP | |
| 8–9 | md+fig | time-vs-mem-energy scatter | correlation | KEEP/**DECIDE** | weaker correlation; keep? |
| 10–11 | md+code | paradigm speed KW/MWU | significance | KEEP | stats |
| 12–13 | md+fig | EDP ranking barh | overall efficiency | KEEP | |
| 14–15 | md+fig | time heatmap per benchmark | per-cell time | KEEP | |

### `notebooks/v2/04_comparative_v2.ipynb`
| # | type | produces | question | KEEP/MERGE/CUT | reason |
|---|------|----------|----------|----------------|--------|
| 0 | md | purpose | — | KEEP | |
| 1–2 | code | setup | — | MERGE→`plot_style` | |
| 3–4 | md+code | multi-metric ranking table | overall ranking | KEEP | |
| 5 | code | export `ranking_summary.csv` | — | KEEP | |
| 6–7 | md+code | normalised efficiency table (ratio vs best) | CLBG-style ranking | KEEP | |
| 8–9 | md+fig | paradigm radar chart | paradigm profile | KEEP/**DECIDE** | radar is debated for thesis rigor; bar alt? |
| 10–11 | md+fig | normalised metrics heatmap | cross-metric profile | KEEP | |
| 12–13 | md+code | top3/bottom3 prints | quick ref | KEEP | text |
| 14–15 | md+code | key-findings print block | citation-ready summary | KEEP | text |

---

## 4. Figures proposed to KEEP as thesis figures (the survivors)
If you approve the cuts above, the thesis-figure set becomes:

- **nb01 (cleaning):** outlier boxplot (methodology appendix)
- **v2/01:** log distributions, coverage heatmap
- **v2/02:** CPU energy boxplot, memory energy boxplot, stacked total energy,
  CPU-vs-mem scatter, energy violins by paradigm, per-benchmark energy heatmap,
  CPU energy ranking
- **v2/03:** time boxplot (log), time-vs-CPU-energy scatter, EDP ranking, time heatmap
- **v2/04:** radar (if kept), normalised heatmap
- **v1/11:** runtime startup disk overhead (corrected)

Everything in **v1/02** and most of **v1/11** retires.

---

## 5. Decisions — RESOLVED ✅ (approved 2026-06-10)

1. **Retire `v1/02_visualization` entirely** — yes (delete the notebook).
2. **Collapse `v1/11` to the startup-overhead figure only** — yes.
3. **Per-paradigm split boxplots** (v2/02 c5,c8; v2/03 c5) — ~~CUT~~ → **REINSTATED**
   later by request (CPU + DRAM in v2/02, execution time on log scale in v2/03).
4. **CO₂ carbon scatter** (v2/02 c20–21) — **CUT** for now.
5. **Radar chart** (v2/04 c8–9) — **CUT**.
6. **nb01 clean-run-count bar** (c8) — **CUT**.
7. **time-vs-mem scatter** (v2/03 c9) — **KEEP**.
8. No further removals.

Also decided for Phase 1/2: `plot_style.py` lives at `notebooks/plot_style.py`;
v2 notebooks are **hand-edited directly** and `generate_notebooks.py` is retired.

### Original questions (for the record)

1. **Retire `v1/02_visualization` entirely?** (Y / keep the per-benchmark grid-bars
   only / keep whole notebook.)
2. **Collapse `v1/11` to just the startup-overhead figure?** (Y / keep more.)
3. **Per-paradigm split boxplots** (v2/02 c5,c8; v2/03 c5): keep alongside the
   all-language boxplot, or CUT as redundant?
4. **CO₂ carbon scatter** (v2/02 c21): keep or CUT (it's energy × constant)?
5. **Radar chart** (v2/04 c9): keep, or replace with a grouped bar?
6. **nb01 clean-run-count bar** (c8): keep or CUT?
7. **time-vs-mem scatter** (v2/03 c9): keep or CUT?
8. Any figure I marked KEEP that you actually want gone — name it.

---

## 6. Phase 1 design note (for when you approve)

`plot_style.py` must be importable from **both** `notebooks/` (v1) and
`notebooks/v2/` (v2). Proposal: place it at `notebooks/v2/plot_style.py` and have v1
notebooks add that dir to `sys.path` (or place it at `notebooks/plot_style.py` and
have v2 add the parent). I'll recommend **`notebooks/v2/plot_style.py`** imported via
a 2-line `sys.path` shim, since the generator already writes into `v2/` and it keeps
the module next to its primary consumers. It will expose: `apply_style()`,
`PARADIGM_COLORS` (Okabe–Ito), `LANGUAGE_ORDER`, `PARADIGM`, `LANG_DISPLAY`,
`MEANPROPS`, `save_fig(fig, name)` (→ 300-dpi vector PDF), and the `COL_*` constants.

---

## 7. Phase 3 — Verification report

**Headless execution:** all 6 surviving notebooks run top-to-bottom with no errors
(`jupyter nbconvert --execute`): `01_data_cleaning`, `11_disk_io_deep_dive`,
`v2/01`–`v2/04`.

**Figures exported:** 17 thesis figures, all 300-dpi **vector PDF** in
`notebooks/figures/` (gitignored). Contact sheet at
`notebooks/figures/_contact_sheet.png` (regenerate from the executed notebooks'
inline PNG outputs).

**Consistency after refactor:**
- ✅ One shared style module (`notebooks/plot_style.py`) imported by every notebook;
  zero inline palette/rcParams duplication.
- ✅ Single Okabe–Ito paradigm palette everywhere (AOT blue / JIT orange /
  Interpreted green); colourblind- and grayscale-safe.
- ✅ Paradigm **membership** now canonical everywhere — fixed the nb11 bug that
  grouped Lua as JIT and dropped F#.
- ✅ All figures titled, axis-labelled with units (J / ms / MB), and meaningfully
  sorted (by mean) or in canonical order.
- ✅ Each figure has a one-line takeaway markdown cell.
- ✅ Fixed a leftover palette collision: the v2/02 stacked total-energy bar used the
  old blue/red; recoloured to a neutral grey + vermillion component pair.

**Known minor items (left as-is, within spec):**
- Horizontal bar charts (rankings, EDP, startup overhead) inherit the global
  **y-only** grid from `apply_style()`; only the startup chart adds an explicit
  x-grid. The Appendix-B style spec mandates a y-only grid, so this is compliant,
  though an x-grid would marginally aid value reading on `barh` charts.
- Figure **titles** are descriptive ("CPU Energy by Language…") rather than
  takeaway-phrased; the takeaway is carried by the markdown cell beneath each figure.
