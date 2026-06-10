# Notebook Refactor Plan — Visualization Consistency & Curation

## Context
Thesis repo benchmarking 18 programming languages across paradigms
(AOT, JIT/VM, Interpreted). Metrics: CPU energy, memory energy, execution time,
measured with the Green Metrics Tool (GMT). Notebooks live in `notebooks/v2/`.

Goal: make every notebook **consistent, readable, and publication-ready**, and
remove exploratory cruft so only thesis-worthy figures remain.

Guiding principle: **every figure must answer a research question.** If a chart
does not support a claim in the thesis, it is a candidate for removal. (Example:
in `11_disk_io_deep_dive`, only "Runtime startup disk overhead per language" is
expected to survive — apply the same judgement everywhere.)

---

## Guardrails — read before doing anything
- Work on a dedicated git branch. Commit after **every** notebook. Never bulk-delete.
- **Audit first, edit later.** Produce the audit, wait for my approval, then refactor.
- Removing a cell or figure is a **proposal** until I approve the cut-list. Relevance
  is tied to the thesis narrative, which I own — do not delete on your own judgement.
- After refactoring a notebook, **execute it top-to-bottom**. It must run clean,
  with no errors and no reliance on manual/out-of-order state.
- Only change *presentation*. Do not alter data-loading behaviour or computed
  values unless you flag it explicitly and I approve.

---

## Definition of Done
- A single shared style module is imported by every notebook. Zero inline
  duplication of palette / rcParams.
- Every language reads the same colour everywhere; every paradigm reads the same
  everywhere.
- Every figure is titled, axis-labelled **with units**, meaningfully sorted, and
  both colourblind- and grayscale-safe.
- Every surviving figure maps to a stated research question. Orphan figures are
  removed (with approval).
- Each notebook opens with a one-line purpose; each figure has a one-line takeaway.
- All thesis figures exported to `figures/` as 300-DPI vector PDF with consistent names.

---

## Phase 0 — Audit (no edits)
For each notebook, produce a table:

| cell idx | type (code/md) | what it produces | question it answers | KEEP / MERGE / CUT | reason |

- Flag figures duplicated across notebooks (same data shown twice).
- Flag dead/exploratory cells (prints, scratch, commented-out code).
- Write the result to `notebooks/v2/AUDIT.md`.
- **Stop and wait for my review of the cut-list before Phase 1.**

---

## Phase 1 — Canonical style
Create `notebooks/v2/plot_style.py` as the single source of truth:

- `apply_style()` — sets matplotlib `rcParams` (font, sizes, dpi, grid).
- `PARADIGM_COLORS` — fixed dict, e.g. `{"AOT": ..., "JIT": ..., "Interpreted": ...}`.
  **Colour by paradigm (3 hues), never 18 per-language hues.**
- `LANGUAGE_ORDER` — fixed list, grouped by paradigm, used for consistent ordering.
- `save_fig(fig, name)` — exports to `figures/<name>.pdf` at 300 DPI, vector.
- Optional helpers: `barplot_by_language(...)`, `add_takeaway(...)`.
- Use a colourblind-safe palette (Okabe–Ito) so figures also survive B&W printing.

---

## Phase 2 — Per-notebook refactor (loop)
For each notebook, in numeric order:
1. Add a top markdown cell: **purpose** + which thesis section it feeds.
2. Apply the KEEP / MERGE / CUT decisions approved in Phase 0.
3. Replace all inline styling with imports from `plot_style`.
4. Run each surviving chart through the **per-figure checklist** (Appendix A) and fix.
5. Add a one-line **takeaway** markdown cell under each figure.
6. Export thesis figures via `save_fig`.
7. Execute clean. Commit: `refactor(nb): <notebook name>`.

---

## Phase 3 — Verify
- Run all notebooks headless (e.g. `jupyter nbconvert --execute`). All must pass.
- Generate a **contact sheet** of every exported figure (one image grid) so I can
  eyeball cross-notebook consistency at a glance.
- Report any leftover inconsistencies: colour mismatches, missing units, unsorted
  categories, charts not matching their data type.

---

## Appendix A — Per-figure checklist
- **Right chart type?** Bars = compare categories. Box/violin = distributions.
  Line = trend over a continuous axis. Avoid pie charts.
- **Variance shown** wherever means are compared? (error bars / CI / box plot)
- **Log scale** if values span more than one order of magnitude?
- **Axis labels include units?** (J, ms, MB, …)
- Categories in **canonical order**, or sorted by value — but consistently.
- Paradigm colours consistent? Use a legend **or** direct labels, not both.
- Readable at thesis column width? Font no smaller than the style baseline.
- **Colourblind- and grayscale-safe?**
- Title states the **takeaway**, not just the variables.

---

## Appendix B — Style spec (starting point; tune inside plot_style.py)
- Font: sans-serif; base 11 pt, title 13 pt.
- Figure: 300 DPI, exported as **PDF (vector)** for LaTeX.
- Paradigm palette (Okabe–Ito, colourblind-safe):
  - AOT = `#0072B2` (blue)
  - JIT/VM = `#E69F00` (orange)
  - Interpreted = `#009E73` (bluish green)
- Grid: light, y-axis only, drawn behind the data.
- Consistent decimal precision across tables and labels.