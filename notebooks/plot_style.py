"""Canonical plotting style for all thesis notebooks (v1 in notebooks/, v2 in
notebooks/v2/).

Single source of truth for: matplotlib rcParams, the paradigm colour palette
(Okabe–Ito, colourblind- and grayscale-safe), language/paradigm metadata, the
measurement column names, and figure export.

Usage from a notebook::

    import sys, pathlib
    # make this module importable regardless of the notebook's location
    sys.path.append(str(pathlib.Path.cwd().parent))   # v2/ notebooks
    sys.path.append(str(pathlib.Path.cwd()))           # notebooks/ (v1)
    import plot_style as ps
    ps.apply_style()
    df = ps.load_runs()                 # per-run frame, display names + paradigm
    df_mean = ps.cell_means(df)         # per-(language × benchmark) means + EDP
    ...
    ps.save_fig(fig, "02_cpu_energy_ranking")

Design notes:
- Colour is assigned by **paradigm** (3 hues), never 18 per-language hues.
- `save_fig` always writes a 300-dpi **vector PDF** into a single shared
  `figures/` directory (next to this module) so cross-notebook figures collect
  in one place for the Phase 3 contact sheet.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
_MODULE_DIR = Path(__file__).resolve().parent          # …/notebooks
_REPO_ROOT = _MODULE_DIR.parent                        # repo root
RESULTS_RUNS_CSV = _REPO_ROOT / "results" / "results_clean_runs.csv"
FIGURES_DIR = _MODULE_DIR / "figures"                  # shared, gitignored

# ── Measurement column names (units already converted by 01_data_cleaning) ─────
COL_CPU_ENERGY = "cpu_energy_rapl_msr_component-package_0-j"
COL_MEM_ENERGY = "memory_energy_rapl_msr_component-dram_0-j"
COL_TIME = "phase_time_syscall_system-system-ms"
COL_CPU_CARBON = "cpu_carbon_rapl_msr_component-package_0-g"
COL_MEM_CARBON = "memory_carbon_rapl_msr_component-dram_0-g"

ALPHA = 0.05  # significance level for the non-parametric tests

# ── Language / paradigm metadata ───────────────────────────────────────────────
# Raw csv code → thesis display name.
LANG_DISPLAY = {
    "c": "C", "cpp": "C++", "csharp": "C#", "fsharp": "F#",
    "nodejs": "JavaScript", "dart": "Dart", "erlang": "Erlang",
    "go": "Go", "haskell": "Haskell", "java": "Java", "lua": "Lua",
    "ocaml": "OCaml", "perl": "Perl", "php": "PHP",
    "python": "Python", "ruby": "Ruby", "rust": "Rust", "swift": "Swift",
}

# Display name → execution paradigm. Canonical classification (matches CLAUDE.md);
# note Lua is Interpreted and F# is JIT — this fixes the nb11 mis-grouping.
PARADIGM = {
    "C": "AOT", "C++": "AOT", "C#": "AOT", "Dart": "AOT", "Go": "AOT",
    "Haskell": "AOT", "Java": "AOT", "OCaml": "AOT", "Rust": "AOT", "Swift": "AOT",
    "Erlang": "JIT", "F#": "JIT", "JavaScript": "JIT", "PHP": "JIT", "Ruby": "JIT",
    "Lua": "Interpreted", "Perl": "Interpreted", "Python": "Interpreted",
}

PARADIGM_ORDER = ["AOT", "JIT", "Interpreted"]

# Okabe–Ito palette — colourblind-safe and distinguishable in grayscale.
PARADIGM_COLORS = {
    "AOT": "#0072B2",          # blue
    "JIT": "#E69F00",          # orange
    "Interpreted": "#009E73",  # bluish green
}

# Canonical language order: grouped by paradigm, alphabetical within group.
# Use for plots that want a fixed order; value-sorted plots sort by value instead.
LANGUAGE_ORDER = (
    sorted(l for l, p in PARADIGM.items() if p == "AOT")
    + sorted(l for l, p in PARADIGM.items() if p == "JIT")
    + sorted(l for l, p in PARADIGM.items() if p == "Interpreted")
)

# Marker style for the mean (▲) overlaid on boxplots/violins (showmeans=True).
MEANPROPS = dict(marker="^", markerfacecolor="white", markeredgecolor="black", markersize=6)


# ── Style ──────────────────────────────────────────────────────────────────────
def apply_style():
    """Apply the canonical matplotlib rcParams for every thesis figure.

    Behaviour: sets a sans-serif font (base 11 pt, title 13 pt), 300-dpi save
    resolution, and a light y-only grid drawn behind the data. Mutates the global
    matplotlib rcParams; no return value. Call once near the top of a notebook.
    """
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"],
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "figure.figsize": (12, 6),
        # light y-only grid, behind the data
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.axisbelow": True,
        "grid.color": "#cccccc",
        "grid.linestyle": "--",
        "grid.linewidth": 0.6,
        "grid.alpha": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def paradigm_color(language: str) -> str:
    """Return the Okabe–Ito colour for a language's paradigm.

    Input: a display-name language (e.g. "Rust"). Returns the hex colour string.
    Raises KeyError if the language is unknown — surfacing a typo rather than
    silently mis-colouring.
    """
    return PARADIGM_COLORS[PARADIGM[language]]


def paradigm_handles(alpha: float = 0.85):
    """Return matplotlib legend handles (one patch per paradigm, in canonical
    order) for a paradigm-coloured plot.

    Input: optional patch alpha. Returns a list of mpatches.Patch suitable for
    ax.legend(handles=...). No side effects.
    """
    import matplotlib.patches as mpatches
    return [mpatches.Patch(color=PARADIGM_COLORS[p], label=p, alpha=alpha)
            for p in PARADIGM_ORDER]


# ── Data loading ────────────────────────────────────────────────────────────────
def load_runs(csv_path: Path | str | None = None) -> pd.DataFrame:
    """Load the per-run cleaned dataset (single source of truth).

    Reads results_clean_runs.csv (default: the repo's results/ copy), maps raw
    language codes to display names, and adds a 'paradigm' column. Returns the
    per-run DataFrame. Raises FileNotFoundError if the csv is missing.
    """
    path = Path(csv_path) if csv_path is not None else RESULTS_RUNS_CSV
    df = pd.read_csv(path)
    df["language"] = df["language"].replace(LANG_DISPLAY)
    df["paradigm"] = df["language"].map(PARADIGM)
    return df


def cell_means(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the per-(language × benchmark) cell means from a per-run frame.

    Input: the per-run DataFrame from load_runs(). Averages every numeric metric
    column within each (language, benchmark) cell, re-attaches 'paradigm', and
    adds an 'EDP' column = (CPU + Memory energy) × time (J·ms). Returns the
    144-row cell-mean DataFrame. This is the building block for the two-step mean.
    """
    id_cols = {"run_id", "measured_at", "language", "benchmark", "paradigm"}
    metric_cols = [c for c in df.columns if c not in id_cols]
    out = df.groupby(["language", "benchmark"])[metric_cols].mean().reset_index()
    out["paradigm"] = out["language"].map(PARADIGM)
    out["EDP"] = (out[COL_CPU_ENERGY] + out[COL_MEM_ENERGY]) * out[COL_TIME]
    return out


def lang_means(df_mean: pd.DataFrame, cols):
    """Per-language two-step mean for column(s) `cols`.

    Inputs: the cell-mean frame from cell_means(), and a column name or list of
    names. Averages the per-benchmark cell means with equal benchmark weight.
    Returns a Series (single column) or DataFrame (list). No side effects.
    """
    return df_mean.groupby("language")[cols].mean()


# ── Export ───────────────────────────────────────────────────────────────────────
def save_fig(fig, name: str, fmt: str = "pdf"):
    """Export a figure to the shared figures/ directory as a 300-dpi vector PDF.

    Inputs: a matplotlib Figure, a base filename (no extension), and an optional
    format. Creates figures/ next to this module if needed and writes
    figures/<name>.<fmt> with tight bounding box. Returns the output Path.
    Side effect: writes a file to disk.
    """
    FIGURES_DIR.mkdir(exist_ok=True)
    out = FIGURES_DIR / f"{name}.{fmt}"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    return out


def add_takeaway(fig, text: str):
    """Add a one-line takeaway caption beneath a figure.

    Inputs: the Figure and the caption text. Draws the text centered below the
    axes in muted italic. Mutates the figure; returns None. Use this when a
    caption should travel with the exported PDF (markdown takeaway cells remain
    the in-notebook narrative).
    """
    fig.text(0.5, -0.04, text, ha="center", va="top",
             fontsize=9, style="italic", color="#555555", wrap=True)


def _tint(hexc, amt=0.82):
    """Mix a hex colour toward white by `amt` (0 = full colour, 1 = white).

    Input: a colour spec and a blend amount. Returns an (r, g, b) tuple. Used to
    make paradigm-coloured table rows light enough to keep black text readable.
    """
    r, g, b = mcolors.to_rgb(hexc)
    return (r + (1 - r) * amt, g + (1 - g) * amt, b + (1 - b) * amt)


def styled_table_fig(df, title, fname, highlight_col=None, row_paradigms=None,
                     figsize=None):
    """Render a DataFrame as a styled table FIGURE for slides/reports.

    Behaviour: draws `df` as a matplotlib table with a dark header, the DataFrame
    index shown as the leading column, and one of two row colourings:
    - if `row_paradigms` is given (a list of paradigm names, one per row in df
      order), each row is tinted by its paradigm colour and a paradigm legend is
      added below the table;
    - otherwise rows are zebra-striped.
    An optional `highlight_col` is tinted green on top of either scheme. Cells are
    rendered with str(), so pass a display-formatted frame (numbers as strings).

    Inputs: a DataFrame (index → first column), a title, a save_fig basename, an
    optional column label to highlight, an optional per-row paradigm list, and an
    optional figsize. Outputs: saves a 300-dpi vector PDF *and* a PNG via save_fig
    and returns the Figure. Side effect: writes two files.
    """
    disp = df.reset_index()
    col_labels = [str(c) for c in disp.columns]
    cell_text = [[f"{v:g}" if isinstance(v, float) else str(v) for v in row]
                 for row in disp.values]
    n_rows, n_cols = disp.shape

    if figsize is None:
        figsize = (2.2 * n_cols + 2, 0.55 * n_rows + 1.5)
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")

    table = ax.table(cellText=cell_text, colLabels=col_labels,
                     cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    table.auto_set_column_width(col=list(range(n_cols)))

    hl = col_labels.index(highlight_col) if highlight_col in col_labels else None
    for j in range(n_cols):                       # header row
        h = table[(0, j)]
        h.set_facecolor("#2c3e50")
        h.set_text_props(color="white", fontweight="bold")
    for i in range(1, n_rows + 1):                # data rows
        for j in range(n_cols):
            cell = table[(i, j)]
            if j == hl:
                cell.set_facecolor("#e3f1ea")
                cell.set_text_props(fontweight="bold", color="#1a7a4c")
            elif row_paradigms is not None:
                cell.set_facecolor(_tint(PARADIGM_COLORS[row_paradigms[i - 1]]))
            else:
                cell.set_facecolor("#f7f8f9" if i % 2 == 0 else "white")
            if j == 0:
                cell.set_text_props(fontweight="bold")

    if row_paradigms is not None:                 # paradigm legend below the table
        handles = [mpatches.Patch(color=PARADIGM_COLORS[p], label=p, alpha=0.85)
                   for p in PARADIGM_ORDER]
        ax.legend(handles=handles, title="Paradigm", loc="lower center",
                  bbox_to_anchor=(0.5, -0.04), ncol=len(PARADIGM_ORDER), frameon=True)

    if title:
        ax.set_title(title, fontsize=12, pad=14, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, fname)                # vector PDF
    save_fig(fig, fname, fmt="png")     # PNG for PowerPoint
    return fig
