#!/usr/bin/env python3
"""Generate v2 benchmark analysis notebooks for the thesis."""

import nbformat as nbf
from pathlib import Path

NB_DIR = Path(__file__).parent
(NB_DIR / "figures").mkdir(exist_ok=True)
(NB_DIR / "outputs").mkdir(exist_ok=True)


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(src):
    return nbf.v4.new_code_cell(src)


def save(notebook, name):
    path = NB_DIR / name
    with open(path, "w") as f:
        nbf.write(notebook, f)
    print(f"Written: {path}")


# ── Shared boilerplate ────────────────────────────────────────────────────────

IMPORTS = """\
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
from itertools import combinations
from pathlib import Path
%matplotlib inline
sns.set_theme(style="whitegrid")
plt.rcParams.update({'figure.dpi': 150, 'savefig.dpi': 150, 'figure.figsize': (12, 6)})"""

_CONSTANTS = """\
# ── Column names as they appear in results_clean_runs.csv ────────────────────
# Units already converted by notebooks/01_data_cleaning.ipynb
COL_CPU_ENERGY = 'cpu_energy_rapl_msr_component-package_0-j'
COL_MEM_ENERGY = 'memory_energy_rapl_msr_component-dram_0-j'
COL_TIME       = 'phase_time_syscall_system-system-s'
COL_CPU_CARBON = 'cpu_carbon_rapl_msr_component-package_0-g'
COL_MEM_CARBON = 'memory_carbon_rapl_msr_component-dram_0-g'

ALPHA = 0.05

FIGURES_DIR = Path('figures')
FIGURES_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR = Path('outputs')
OUTPUTS_DIR.mkdir(exist_ok=True)

LANG_DISPLAY = {
    'c': 'C', 'cpp': 'C++', 'csharp': 'C#', 'fsharp': 'F#',
    'nodejs': 'JavaScript', 'dart': 'Dart', 'erlang': 'Erlang',
    'go': 'Go', 'haskell': 'Haskell', 'java': 'Java', 'lua': 'Lua',
    'ocaml': 'OCaml', 'perl': 'Perl', 'php': 'PHP',
    'python': 'Python', 'ruby': 'Ruby', 'rust': 'Rust', 'swift': 'Swift',
}

PARADIGM = {
    'C': 'AOT', 'C++': 'AOT', 'C#': 'AOT', 'Dart': 'AOT', 'Go': 'AOT',
    'Haskell': 'AOT', 'Java': 'AOT', 'OCaml': 'AOT', 'Rust': 'AOT', 'Swift': 'AOT',
    'Erlang': 'JIT', 'F#': 'JIT', 'JavaScript': 'JIT', 'PHP': 'JIT', 'Ruby': 'JIT',
    'Lua': 'Interpreted', 'Perl': 'Interpreted', 'Python': 'Interpreted',
}

PARADIGM_COLORS = {'AOT': '#2980b9', 'JIT': '#e67e22', 'Interpreted': '#27ae60'}
PARADIGM_ORDER  = ['AOT', 'JIT', 'Interpreted']"""

_LOAD_AND_CONVERT = """\
# Data pre-cleaned by notebooks/01_data_cleaning.ipynb:
#   - Outliers removed per (language × benchmark) group, IQR fence on CPU energy + time
#   - Units already converted (J, s, g, MB, W)
df = pd.read_csv('../../results/results_clean_runs.csv')
df['language'] = df['language'].replace(LANG_DISPLAY)
df['paradigm'] = df['language'].map(PARADIGM)

print(f"Shape: {df.shape}")
print(f"Languages ({df['language'].nunique()}): {sorted(df['language'].unique())}")
print(f"Benchmarks ({df['benchmark'].nunique()}): {sorted(df['benchmark'].unique())}")
print("Units: energy=J | time=s | carbon=g | disk/net=MB | power=W")
df.head(3)"""

# Shared setup for all notebooks — no inline cleaning or conversion needed
CONSTANTS_AND_LOAD = _CONSTANTS + "\n\n" + _LOAD_AND_CONVERT


# ═════════════════════════════════════════════════════════════════════════════
# Notebook 01 – Data Profiling & Quality
# ═════════════════════════════════════════════════════════════════════════════

def make_nb01():
    n = nbf.v4.new_notebook()
    n.cells = [
        md("""\
# 01 · Data Profiling & Quality

This notebook profiles the **pre-cleaned** benchmark dataset before analysis.
Cleaning (outlier removal + unit conversion) was already performed by
`notebooks/01_data_cleaning.ipynb`, which produced `results/results_clean_runs.csv`.

**Cleaning pipeline (upstream):**
- Outliers removed per **(language × benchmark)** group using the 1.5×IQR boxplot fence,
  applied to both CPU energy and execution time
- Units converted: µJ → J, µs → s, µg → g, Bytes → MB, mW → W

**This notebook covers:**
- Column overview and descriptive statistics
- Missing value check
- Metric distributions
- Data coverage (languages × benchmarks)
- Per-language summary table

**Dataset:** 18 languages × 8 benchmarks, measured with the Green Metrics Tool (GMT).
**Priority metrics:** CPU Energy (J), Memory Energy (J), Execution Time (s)"""),

        code(IMPORTS),

        code(CONSTANTS_AND_LOAD),

        md("""\
## 1. Column Overview

Extended `describe()` supplemented with median and IQR for the three priority columns.
Median is preferred over mean for right-skewed benchmark distributions.
All values are in human-readable units (J for energy, s for time)."""),

        code("""\
priority = [COL_CPU_ENERGY, COL_MEM_ENERGY, COL_TIME]
labels   = {COL_CPU_ENERGY: 'CPU Energy (J)',
            COL_MEM_ENERGY: 'Mem Energy (J)',
            COL_TIME:       'Time (s)'}

stats_tbl = df[priority].describe().T
stats_tbl['median'] = df[priority].median()
stats_tbl['IQR']    = df[priority].quantile(0.75) - df[priority].quantile(0.25)
stats_tbl['skew']   = df[priority].skew()
stats_tbl.index     = [labels[c] for c in stats_tbl.index]
stats_tbl.round(4)"""),

        md("""\
## 2. Missing Values

Completeness check across all 16 columns. Benchmark datasets often contain zeros rather
than NaN for metrics that were not triggered (e.g. network bytes on a CPU-only task)."""),

        code("""\
null_counts = df.isnull().sum()
if null_counts.sum() == 0:
    print("✓ No missing values — dataset is complete.")
else:
    print("Missing values detected:")
    print(null_counts[null_counts > 0])

# Check for zero-only columns (may indicate inactive metrics)
zero_frac = (df[priority] == 0).mean()
print("\\nFraction of zeros in priority columns:")
for col, frac in zip(['CPU Energy', 'Mem Energy', 'Time'], zero_frac):
    print(f"  {col}: {frac:.1%}")"""),

        md("""\
## 3. Distributions

Histograms on a log₁₀ scale for the three priority metrics.
Benchmark data is typically right-skewed (a few languages/benchmarks dominate the upper tail).
Values are in J (energy) and s (time).
A divergence of >20% between mean and median is flagged."""),

        code("""\
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
metric_info = [
    ('CPU Energy', COL_CPU_ENERGY, 'J'),
    ('Memory Energy', COL_MEM_ENERGY, 'J'),
    ('Execution Time', COL_TIME, 's'),
]
for ax, (label, col, unit) in zip(axes, metric_info):
    vals = df[col][df[col] > 0]
    log_vals = np.log10(vals)
    ax.hist(log_vals, bins=40, color='steelblue', edgecolor='white', alpha=0.85)
    mean_v, med_v = vals.mean(), vals.median()
    ax.axvline(np.log10(mean_v), color='red',    linestyle='--', label=f'mean={mean_v:.2f} {unit}')
    ax.axvline(np.log10(med_v),  color='orange', linestyle='-',  label=f'median={med_v:.2f} {unit}')
    ax.set_title(f'{label}')
    ax.set_xlabel(f'log₁₀({unit})')
    ax.set_ylabel('Count')
    ax.legend(fontsize=8)
    if abs(mean_v - med_v) / med_v > 0.20:
        ax.set_title(ax.get_title() + '\\n⚠ mean/median diverge >20%')

fig.suptitle('Priority Metric Distributions (log₁₀ scale)', fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'distributions.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 4. Data Coverage

Heatmap showing the number of runs for each language × benchmark pair.
A uniform count across all cells indicates balanced coverage."""),

        code("""\
coverage = df.groupby(['language', 'benchmark']).size().unstack(fill_value=0)

fig, ax = plt.subplots(figsize=(13, 8))
sns.heatmap(coverage, annot=True, fmt='d', cmap='Blues', ax=ax,
            linewidths=0.4, linecolor='#ccc',
            cbar_kws={'label': 'Number of runs'})
ax.set_title('Data Coverage: Runs per Language × Benchmark', fontsize=13)
ax.set_xlabel('Benchmark')
ax.set_ylabel('Language')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'coverage_heatmap.png', bbox_inches='tight')
plt.show()
print(f"Min runs in any cell: {coverage.values.min()}")
print(f"Max runs in any cell: {coverage.values.max()}")
print(f"Mean runs per cell:   {coverage.values.mean():.1f}")"""),

        md("""\
## 5. Summary Table

Per-language descriptive statistics for all three priority metrics in human-readable units.
Mean and median are both reported; large divergence signals skewness within a language."""),

        code("""\
summary_tbl = df.groupby('language').agg(
    paradigm      = ('paradigm', 'first'),
    runs          = ('run_id', 'count'),
    cpu_mean_J    = (COL_CPU_ENERGY, 'mean'),
    cpu_median_J  = (COL_CPU_ENERGY, 'median'),
    mem_mean_J    = (COL_MEM_ENERGY, 'mean'),
    mem_median_J  = (COL_MEM_ENERGY, 'median'),
    time_mean_s   = (COL_TIME, 'mean'),
    time_median_s = (COL_TIME, 'median'),
).round(4)

# Flag skew
for label, mc, mdc in [('CPU energy', 'cpu_mean_J', 'cpu_median_J'),
                        ('Mem energy', 'mem_mean_J', 'mem_median_J'),
                        ('Time',       'time_mean_s','time_median_s')]:
    skew_mask = (abs(summary_tbl[mc] - summary_tbl[mdc]) / summary_tbl[mdc]) > 0.20
    if skew_mask.any():
        print(f"⚠ {label} mean/median diverge >20% for: {list(summary_tbl.index[skew_mask])}")

summary_tbl.sort_values('cpu_median_J')"""),
    ]
    save(n, "01_data_profiling_v2.ipynb")


# ═════════════════════════════════════════════════════════════════════════════
# Notebook 02 – Energy Analysis (Priority)
# ═════════════════════════════════════════════════════════════════════════════

def make_nb02():
    n = nbf.v4.new_notebook()
    n.cells = [
        md("""\
# 02 · Energy Analysis ⭐

This is the core analysis notebook for the thesis. It provides a deep dive into CPU and
Memory energy consumption across 18 languages, grouped by execution paradigm (AOT, JIT,
Interpreted).

**Units:** All energy values are in **Joules (J)** (converted from raw µJ at load time).

**Key questions:**
- Which languages are most energy-efficient?
- Do paradigms (AOT vs JIT vs Interpreted) differ significantly in energy consumption?
- How does energy vary across benchmarks?

**Statistical methodology:**
Benchmark distributions are typically right-skewed and non-normal. We therefore use:
- **Median** as the primary central-tendency measure
- **Kruskal-Wallis** (non-parametric ANOVA) for paradigm comparisons
- **Mann-Whitney U** (pairwise) with **Bonferroni correction** for post-hoc tests
- **Rank-biserial correlation** as the effect size measure"""),

        code(IMPORTS),

        code(CONSTANTS_AND_LOAD),

        md("""\
## 1. CPU Energy by Language

Boxplots sorted by median CPU energy (J). Lower is better (more energy-efficient).
Each paradigm group is shown separately to highlight within-group spread."""),

        code("""\
lang_order_cpu = (df.groupby('language')[COL_CPU_ENERGY]
                    .median()
                    .sort_values()
                    .index.tolist())

fig, ax = plt.subplots(figsize=(15, 6))
bp = ax.boxplot(
    [df[df['language'] == lang][COL_CPU_ENERGY].values for lang in lang_order_cpu],
    labels=lang_order_cpu, patch_artist=True, notch=False,
    medianprops=dict(color='black', linewidth=2),
    flierprops=dict(marker='x', markerfacecolor='red', markersize=5, alpha=0.6),
)
for patch, lang in zip(bp['boxes'], lang_order_cpu):
    patch.set_facecolor(PARADIGM_COLORS[PARADIGM[lang]])
    patch.set_alpha(0.75)

for i, lang in enumerate(lang_order_cpu):
    med = df[df['language'] == lang][COL_CPU_ENERGY].median()
    ax.text(i + 1, med, f'{med:.1f}', ha='center', va='bottom', fontsize=7, color='black')

legend_handles = [mpatches.Patch(color=PARADIGM_COLORS[p], label=p, alpha=0.75)
                  for p in PARADIGM_ORDER]
ax.legend(handles=legend_handles, title='Paradigm', loc='upper left')
ax.set_title('CPU Energy by Language (sorted by median)', fontsize=13)
ax.set_xlabel('Language')
ax.set_ylabel('CPU Energy (J)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'cpu_energy_by_language.png', bbox_inches='tight')
plt.show()"""),

        code("""\
fig, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=False)
for ax, paradigm in zip(axes, PARADIGM_ORDER):
    langs = [l for l in lang_order_cpu if PARADIGM[l] == paradigm]
    data  = [df[df['language'] == l][COL_CPU_ENERGY].values for l in langs]
    bp = ax.boxplot(data, labels=langs, patch_artist=True,
                    medianprops=dict(color='black', linewidth=2),
                    flierprops=dict(marker='x', markerfacecolor='red', markersize=5, alpha=0.6))
    for patch in bp['boxes']:
        patch.set_facecolor(PARADIGM_COLORS[paradigm])
        patch.set_alpha(0.75)
    ax.set_title(f'{paradigm} Languages')
    ax.set_ylabel('CPU Energy (J)' if paradigm == 'AOT' else '')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

fig.suptitle('CPU Energy by Paradigm Group (J)', fontsize=13)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'cpu_energy_per_paradigm.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 2. Memory Energy by Language

Same structure as CPU energy. Memory energy (J) reflects DRAM power draw, which varies
less across paradigms but reveals GC pressure and allocation patterns."""),

        code("""\
lang_order_mem = (df.groupby('language')[COL_MEM_ENERGY]
                    .median()
                    .sort_values()
                    .index.tolist())

fig, ax = plt.subplots(figsize=(15, 6))
bp = ax.boxplot(
    [df[df['language'] == lang][COL_MEM_ENERGY].values for lang in lang_order_mem],
    labels=lang_order_mem, patch_artist=True,
    medianprops=dict(color='black', linewidth=2),
    flierprops=dict(marker='x', markerfacecolor='red', markersize=5, alpha=0.6),
)
for patch, lang in zip(bp['boxes'], lang_order_mem):
    patch.set_facecolor(PARADIGM_COLORS[PARADIGM[lang]])
    patch.set_alpha(0.75)

for i, lang in enumerate(lang_order_mem):
    med = df[df['language'] == lang][COL_MEM_ENERGY].median()
    ax.text(i + 1, med, f'{med:.3f}', ha='center', va='bottom', fontsize=7)

legend_handles = [mpatches.Patch(color=PARADIGM_COLORS[p], label=p, alpha=0.75)
                  for p in PARADIGM_ORDER]
ax.legend(handles=legend_handles, title='Paradigm', loc='upper left')
ax.set_title('Memory Energy by Language (sorted by median)', fontsize=13)
ax.set_xlabel('Language')
ax.set_ylabel('Memory Energy (J)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'mem_energy_by_language.png', bbox_inches='tight')
plt.show()"""),

        code("""\
fig, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=False)
for ax, paradigm in zip(axes, PARADIGM_ORDER):
    langs = [l for l in lang_order_mem if PARADIGM[l] == paradigm]
    data  = [df[df['language'] == l][COL_MEM_ENERGY].values for l in langs]
    bp = ax.boxplot(data, labels=langs, patch_artist=True,
                    medianprops=dict(color='black', linewidth=2),
                    flierprops=dict(marker='x', markerfacecolor='red', markersize=5, alpha=0.6))
    for patch in bp['boxes']:
        patch.set_facecolor(PARADIGM_COLORS[paradigm])
        patch.set_alpha(0.75)
    ax.set_title(f'{paradigm} Languages')
    ax.set_ylabel('Memory Energy (J)' if paradigm == 'AOT' else '')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

fig.suptitle('Memory Energy by Paradigm Group (J)', fontsize=13)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'mem_energy_per_paradigm.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 3. CPU + Memory Energy Combined

Two complementary views:
1. **Stacked bar chart** — total energy (CPU + Memory) per language in Joules, split by component
2. **Scatter plot** — CPU vs Memory energy (J), to identify languages where one dominates"""),

        code("""\
agg = df.groupby('language')[[COL_CPU_ENERGY, COL_MEM_ENERGY]].median()
agg = agg.sort_values(COL_CPU_ENERGY)
agg['paradigm'] = agg.index.map(PARADIGM)

fig, ax = plt.subplots(figsize=(14, 6))
x = np.arange(len(agg))
ax.bar(x, agg[COL_CPU_ENERGY], label='CPU Energy (J)', color='#2980b9', alpha=0.85)
ax.bar(x, agg[COL_MEM_ENERGY], bottom=agg[COL_CPU_ENERGY],
       label='Memory Energy (J)', color='#e74c3c', alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(agg.index, rotation=45, ha='right')
ax.set_title('Total Energy (CPU + Memory) by Language — median across all benchmarks', fontsize=12)
ax.set_ylabel('Energy (J)')
ax.legend()
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'total_energy_stacked.png', bbox_inches='tight')
plt.show()"""),

        code("""\
fig, ax = plt.subplots(figsize=(10, 7))
for paradigm in PARADIGM_ORDER:
    langs = [l for l in agg.index if agg.loc[l, 'paradigm'] == paradigm]
    ax.scatter(
        agg.loc[langs, COL_CPU_ENERGY],
        agg.loc[langs, COL_MEM_ENERGY],
        color=PARADIGM_COLORS[paradigm], label=paradigm, s=80, zorder=3
    )
    for lang in langs:
        ax.annotate(lang,
                    (agg.loc[lang, COL_CPU_ENERGY], agg.loc[lang, COL_MEM_ENERGY]),
                    textcoords='offset points', xytext=(6, 4), fontsize=8)

ax.set_title('CPU Energy vs Memory Energy — median per language (J)', fontsize=12)
ax.set_xlabel('CPU Energy (J)')
ax.set_ylabel('Memory Energy (J)')
ax.legend(title='Paradigm')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'cpu_vs_mem_scatter.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 4. Paradigm Comparison

**Violin plots** show the full distribution shape per paradigm.
**Kruskal-Wallis** tests whether any paradigm differs significantly.
If significant, **pairwise Mann-Whitney U** tests with **Bonferroni correction** identify which pairs differ.
Effect size is reported as **rank-biserial correlation** r = 1 − 2U/(n₁·n₂)."""),

        code("""\
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
for ax, col, label in zip(axes,
                           [COL_CPU_ENERGY, COL_MEM_ENERGY],
                           ['CPU Energy (J)', 'Memory Energy (J)']):
    groups = [df[df['paradigm'] == p][col].values for p in PARADIGM_ORDER]
    parts  = ax.violinplot(groups, positions=range(len(PARADIGM_ORDER)), showmedians=True)
    for pc, p in zip(parts['bodies'], PARADIGM_ORDER):
        pc.set_facecolor(PARADIGM_COLORS[p])
        pc.set_alpha(0.7)
    ax.set_xticks(range(len(PARADIGM_ORDER)))
    ax.set_xticklabels(PARADIGM_ORDER)
    ax.set_title(f'{label} by Paradigm')
    ax.set_ylabel(label)

fig.suptitle('Energy Distribution by Execution Paradigm', fontsize=13)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'energy_violin_paradigm.png', bbox_inches='tight')
plt.show()"""),

        code("""\
def rank_biserial(x, y):
    \"\"\"Rank-biserial correlation as effect size for Mann-Whitney U.\"\"\"
    u, _ = stats.mannwhitneyu(x, y, alternative='two-sided')
    return 1 - (2 * u) / (len(x) * len(y))

for col, label in [(COL_CPU_ENERGY, 'CPU Energy (J)'), (COL_MEM_ENERGY, 'Memory Energy (J)')]:
    groups   = {p: df[df['paradigm'] == p][col].values for p in PARADIGM_ORDER}
    kw_stat, kw_p = stats.kruskal(*groups.values())
    n_pairs = len(PARADIGM_ORDER) * (len(PARADIGM_ORDER) - 1) // 2

    print(f"\\n{'='*60}")
    print(f"{label}")
    print(f"  Kruskal-Wallis H={kw_stat:.3f}, p={kw_p:.4f} ", end='')
    print("(SIGNIFICANT)" if kw_p < ALPHA else "(not significant)")

    if kw_p < ALPHA:
        print(f"  Post-hoc Mann-Whitney U (Bonferroni α={ALPHA/n_pairs:.4f}):")
        for (p1, p2) in combinations(PARADIGM_ORDER, 2):
            u, p = stats.mannwhitneyu(groups[p1], groups[p2], alternative='two-sided')
            p_adj = min(p * n_pairs, 1.0)
            r = rank_biserial(groups[p1], groups[p2])
            sig = "✓" if p_adj < ALPHA else "✗"
            print(f"    {sig} {p1} vs {p2}: U={u:.0f}, p_adj={p_adj:.4f}, r={r:.3f}")"""),

        md("""\
## 5. Per-Benchmark Energy Heatmap

Heatmap of median CPU and Memory energy (J) for each language × benchmark combination.
This reveals which benchmarks are most energy-intensive and which languages suffer
disproportionately on specific workloads."""),

        code("""\
pivot_cpu = df.groupby(['language', 'benchmark'])[COL_CPU_ENERGY].median().unstack()
pivot_mem = df.groupby(['language', 'benchmark'])[COL_MEM_ENERGY].median().unstack()

lang_sort = df.groupby('language')[COL_CPU_ENERGY].median().sort_values().index
pivot_cpu = pivot_cpu.loc[lang_sort]
pivot_mem = pivot_mem.loc[lang_sort]

fig, axes = plt.subplots(1, 2, figsize=(18, 9))
for ax, pivot, title in zip(axes,
                              [pivot_cpu, pivot_mem],
                              ['CPU Energy (J) — median', 'Memory Energy (J) — median']):
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
                linewidths=0.3, cbar_kws={'label': 'Energy (J)'})
    ax.set_title(title, fontsize=11)
    ax.set_xlabel('Benchmark')
    ax.set_ylabel('Language')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

fig.suptitle('Per-Benchmark Energy Heatmap — sorted by median CPU energy (J)', fontsize=13)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'energy_heatmap_benchmark.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 6. Energy Efficiency Ranking

Languages ranked by median CPU energy (J) ascending — lower rank = more efficient.
A combined rank averages CPU and Memory energy ranks."""),

        code("""\
rank_agg = df.groupby('language').agg(
    paradigm       = ('paradigm', 'first'),
    cpu_mean_J     = (COL_CPU_ENERGY, 'mean'),
    cpu_median_J   = (COL_CPU_ENERGY, 'median'),
    mem_mean_J     = (COL_MEM_ENERGY, 'mean'),
    mem_median_J   = (COL_MEM_ENERGY, 'median'),
)
rank_agg['cpu_rank'] = rank_agg['cpu_median_J'].rank().astype(int)
rank_agg['mem_rank'] = rank_agg['mem_median_J'].rank().astype(int)
rank_agg['combined_rank'] = ((rank_agg['cpu_rank'] + rank_agg['mem_rank']) / 2).round(1)
ranking = rank_agg.sort_values('combined_rank')
ranking.index.name = 'Language'
ranking[['paradigm', 'cpu_median_J', 'mem_median_J', 'cpu_rank', 'mem_rank', 'combined_rank']]"""),

        code("""\
fig, ax = plt.subplots(figsize=(12, 7))
colors = [PARADIGM_COLORS[PARADIGM[l]] for l in ranking.index]
ax.barh(ranking.index, ranking['cpu_median_J'], color=colors, alpha=0.85, edgecolor='white')
ax.set_title('CPU Energy Efficiency Ranking — median across all benchmarks (J)', fontsize=12)
ax.set_xlabel('Median CPU Energy (J)')
ax.set_ylabel('Language')
ax.invert_yaxis()
legend_handles = [mpatches.Patch(color=PARADIGM_COLORS[p], label=p, alpha=0.85)
                  for p in PARADIGM_ORDER]
ax.legend(handles=legend_handles, title='Paradigm', loc='lower right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'cpu_energy_ranking.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 7. CO₂ Carbon Correlation

CPU carbon (g CO₂) is derived from CPU energy via a carbon-intensity factor.
We verify the correlation and check whether it is simply proportional or shows variance.
Values are in grams (g) — converted from raw µg at load time."""),

        code("""\
cpu_carbon_nonzero = (df[COL_CPU_CARBON] != 0).mean()
print(f"Non-zero CPU carbon values: {cpu_carbon_nonzero:.1%}")

if cpu_carbon_nonzero > 0.5:
    spearman_r, spearman_p = stats.spearmanr(df[COL_CPU_ENERGY], df[COL_CPU_CARBON])
    print(f"Spearman r(CPU energy J, CPU carbon g) = {spearman_r:.4f}, p = {spearman_p:.2e}")

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(df[COL_CPU_ENERGY], df[COL_CPU_CARBON], alpha=0.3, s=20, color='steelblue')
    ax.set_xlabel('CPU Energy (J)')
    ax.set_ylabel('CPU Carbon (g CO₂)')
    ax.set_title(f'CPU Energy (J) vs CPU Carbon (g) — Spearman r={spearman_r:.3f}')
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'cpu_energy_vs_carbon.png', bbox_inches='tight')
    plt.show()
else:
    print("CPU carbon column is mostly zero — likely not recorded for this dataset.")"""),
    ]
    save(n, "02_energy_analysis_v2.ipynb")


# ═════════════════════════════════════════════════════════════════════════════
# Notebook 03 – Time Analysis
# ═════════════════════════════════════════════════════════════════════════════

def make_nb03():
    n = nbf.v4.new_notebook()
    n.cells = [
        md("""\
# 03 · Execution Time Analysis

This notebook analyses execution time across languages and its relationship to energy.

**Units:** Time values are in **seconds (s)** (converted from raw µs at load time).
Energy values are in **Joules (J)**.

**Key questions:**
- Which languages execute fastest?
- How does time correlate with CPU and memory energy?
- What is the Energy-Delay Product (EDP = CPU energy × time, in J·s)?

**Statistical note:** Spearman correlation is used throughout (more robust than Pearson
for right-skewed benchmark data)."""),

        code(IMPORTS),

        code(CONSTANTS_AND_LOAD),

        md("""\
## 1. Execution Time by Language

Boxplots sorted by median execution time (s). Log scale is used because time spans several
orders of magnitude across languages and benchmarks."""),

        code("""\
lang_order_time = (df.groupby('language')[COL_TIME]
                     .median()
                     .sort_values()
                     .index.tolist())

fig, ax = plt.subplots(figsize=(15, 6))
bp = ax.boxplot(
    [df[df['language'] == lang][COL_TIME].values for lang in lang_order_time],
    labels=lang_order_time, patch_artist=True,
    medianprops=dict(color='black', linewidth=2),
    flierprops=dict(marker='x', markerfacecolor='red', markersize=5, alpha=0.6),
)
for patch, lang in zip(bp['boxes'], lang_order_time):
    patch.set_facecolor(PARADIGM_COLORS[PARADIGM[lang]])
    patch.set_alpha(0.75)

ax.set_yscale('log')
ax.set_title('Execution Time by Language — log scale (sorted by median)', fontsize=13)
ax.set_xlabel('Language')
ax.set_ylabel('Execution Time (s, log scale)')
legend_handles = [mpatches.Patch(color=PARADIGM_COLORS[p], label=p, alpha=0.75)
                  for p in PARADIGM_ORDER]
ax.legend(handles=legend_handles, title='Paradigm', loc='upper left')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'time_by_language.png', bbox_inches='tight')
plt.show()"""),

        code("""\
fig, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=False)
for ax, paradigm in zip(axes, PARADIGM_ORDER):
    langs = [l for l in lang_order_time if PARADIGM[l] == paradigm]
    data  = [df[df['language'] == l][COL_TIME].values for l in langs]
    bp = ax.boxplot(data, labels=langs, patch_artist=True,
                    medianprops=dict(color='black', linewidth=2),
                    flierprops=dict(marker='x', markerfacecolor='red', markersize=5, alpha=0.6))
    for patch in bp['boxes']:
        patch.set_facecolor(PARADIGM_COLORS[paradigm])
        patch.set_alpha(0.75)
    ax.set_yscale('log')
    ax.set_title(f'{paradigm}')
    ax.set_ylabel('Time (s, log)' if paradigm == 'AOT' else '')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

fig.suptitle('Execution Time per Paradigm Group — log scale (s)', fontsize=13)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'time_per_paradigm.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 2. Time vs CPU Energy

Scatter plot of median execution time (s) vs median CPU energy (J) per language.
A strong correlation is expected. The quadrants reveal interesting outliers:
- **Top-left**: fast but energy-hungry (parallel overhead?)
- **Bottom-right**: slow but energy-efficient"""),

        code("""\
agg_time = df.groupby('language').agg(
    time_med   = (COL_TIME, 'median'),
    cpu_med    = (COL_CPU_ENERGY, 'median'),
    mem_med    = (COL_MEM_ENERGY, 'median'),
    paradigm   = ('paradigm', 'first'),
).reset_index()

r, p = stats.spearmanr(agg_time['time_med'], agg_time['cpu_med'])
print(f"Spearman r(time s, CPU energy J) = {r:.4f}, p = {p:.4f}")

fig, ax = plt.subplots(figsize=(10, 7))
for paradigm in PARADIGM_ORDER:
    sub = agg_time[agg_time['paradigm'] == paradigm]
    ax.scatter(sub['time_med'], sub['cpu_med'],
               color=PARADIGM_COLORS[paradigm], label=paradigm, s=80, zorder=3)
    for _, row in sub.iterrows():
        ax.annotate(row['language'],
                    (row['time_med'], row['cpu_med']),
                    textcoords='offset points', xytext=(6, 3), fontsize=8)

ax.set_xlabel('Median Execution Time (s)')
ax.set_ylabel('Median CPU Energy (J)')
ax.set_title(f'Execution Time (s) vs CPU Energy (J) — Spearman r={r:.3f}, p={p:.3f}', fontsize=12)
ax.legend(title='Paradigm')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'time_vs_cpu_energy.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 3. Time vs Memory Energy

Same analysis for Memory Energy (J). Memory energy tends to correlate less tightly with
time because DRAM power draw depends more on allocation patterns than execution duration."""),

        code("""\
r_mem, p_mem = stats.spearmanr(agg_time['time_med'], agg_time['mem_med'])
print(f"Spearman r(time s, Memory energy J) = {r_mem:.4f}, p = {p_mem:.4f}")

fig, ax = plt.subplots(figsize=(10, 7))
for paradigm in PARADIGM_ORDER:
    sub = agg_time[agg_time['paradigm'] == paradigm]
    ax.scatter(sub['time_med'], sub['mem_med'],
               color=PARADIGM_COLORS[paradigm], label=paradigm, s=80, zorder=3)
    for _, row in sub.iterrows():
        ax.annotate(row['language'],
                    (row['time_med'], row['mem_med']),
                    textcoords='offset points', xytext=(6, 3), fontsize=8)

ax.set_xlabel('Median Execution Time (s)')
ax.set_ylabel('Median Memory Energy (J)')
ax.set_title(f'Execution Time (s) vs Memory Energy (J) — Spearman r={r_mem:.3f}, p={p_mem:.3f}', fontsize=12)
ax.legend(title='Paradigm')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'time_vs_mem_energy.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 4. Paradigm Speed Comparison

Kruskal-Wallis test on execution time across paradigm groups, followed by pairwise
Mann-Whitney U tests with Bonferroni correction."""),

        code("""\
def rank_biserial(x, y):
    u, _ = stats.mannwhitneyu(x, y, alternative='two-sided')
    return 1 - (2 * u) / (len(x) * len(y))

groups = {p: df[df['paradigm'] == p][COL_TIME].values for p in PARADIGM_ORDER}
kw_stat, kw_p = stats.kruskal(*groups.values())
n_pairs = len(PARADIGM_ORDER) * (len(PARADIGM_ORDER) - 1) // 2

print(f"Kruskal-Wallis (Execution Time, s): H={kw_stat:.3f}, p={kw_p:.4f}")
print("SIGNIFICANT" if kw_p < ALPHA else "Not significant")

if kw_p < ALPHA:
    print(f"\\nPost-hoc (Bonferroni α={ALPHA/n_pairs:.4f}):")
    for p1, p2 in combinations(PARADIGM_ORDER, 2):
        u, p = stats.mannwhitneyu(groups[p1], groups[p2], alternative='two-sided')
        p_adj = min(p * n_pairs, 1.0)
        r = rank_biserial(groups[p1], groups[p2])
        sig = "✓" if p_adj < ALPHA else "✗"
        print(f"  {sig} {p1} vs {p2}: p_adj={p_adj:.4f}, r={r:.3f}")"""),

        md("""\
## 5. Energy-Delay Product (EDP)

**EDP = (CPU Energy + Memory Energy) (J) × Execution Time (s)** — unit: **J·s**

EDP is a standard hardware metric penalising both slow and energy-hungry implementations.
Including memory energy captures the full energy cost of execution. Lower EDP is better."""),

        code("""\
df['EDP'] = (df[COL_CPU_ENERGY] + df[COL_MEM_ENERGY]) * df[COL_TIME]  # J · s

edp_rank = (df.groupby('language')['EDP']
              .median()
              .sort_values()
              .reset_index())
edp_rank.columns = ['language', 'EDP_median_Js']
edp_rank['paradigm'] = edp_rank['language'].map(PARADIGM)

print("EDP Ranking — lower is better (unit: J·s):")
print(edp_rank[['language', 'paradigm', 'EDP_median_Js']].to_string(index=False))

fig, ax = plt.subplots(figsize=(12, 7))
colors = [PARADIGM_COLORS[p] for p in edp_rank['paradigm']]
ax.barh(edp_rank['language'], edp_rank['EDP_median_Js'], color=colors, alpha=0.85, edgecolor='white')
ax.set_title('Energy-Delay Product Ranking — CPU Energy × Time (J·s, median)', fontsize=12)
ax.set_xlabel('EDP (J·s)')
ax.set_ylabel('Language')
ax.invert_yaxis()
legend_handles = [mpatches.Patch(color=PARADIGM_COLORS[p], label=p, alpha=0.85)
                  for p in PARADIGM_ORDER]
ax.legend(handles=legend_handles, title='Paradigm', loc='lower right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'edp_ranking.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 6. Benchmark-Level Time Heatmap

Median execution time (s) for each language × benchmark cell. Reveals which benchmarks
are the slowest and which languages suffer most on specific workloads."""),

        code("""\
pivot_time = (df.groupby(['language', 'benchmark'])[COL_TIME]
                .median()
                .unstack())
lang_sort = df.groupby('language')[COL_TIME].median().sort_values().index
pivot_time = pivot_time.loc[lang_sort]

fig, ax = plt.subplots(figsize=(13, 9))
sns.heatmap(pivot_time, annot=True, fmt='.2f', cmap='YlOrRd', ax=ax,
            linewidths=0.3, cbar_kws={'label': 'Time (s)'})
ax.set_title('Execution Time Heatmap — median (s)', fontsize=12)
ax.set_xlabel('Benchmark')
ax.set_ylabel('Language')
plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'time_heatmap_benchmark.png', bbox_inches='tight')
plt.show()"""),
    ]
    save(n, "03_time_analysis_v2.ipynb")


# ═════════════════════════════════════════════════════════════════════════════
# Notebook 04 – Comparative Summary
# ═════════════════════════════════════════════════════════════════════════════

def make_nb04():
    n = nbf.v4.new_notebook()
    n.cells = [
        md("""\
# 04 · Comparative Summary

This notebook synthesises results from notebooks 02 and 03 into a single cross-metric
comparison suitable for the thesis results chapter.

**Units:**
- Energy → **J** (Joules)
- Time → **s** (seconds)
- EDP → **J·s** (Joule-seconds)

**Outputs:**
- `outputs/ranking_summary.csv` — full multi-metric ranking table
- Radar chart per paradigm
- Normalised metrics heatmap
- Top 3 / Bottom 3 per metric
- Key findings bullet list"""),

        code(IMPORTS),

        code(CONSTANTS_AND_LOAD),

        md("""\
## 1. Multi-Metric Ranking Table

Each language is ranked (1 = best) on four metrics:
- Mean CPU Energy (J)
- Mean Memory Energy (J)
- Mean Execution Time (s)
- Mean EDP — (CPU + Memory Energy) × Time (J·s)

Values use benchmark-level means averaged across all 8 benchmarks (equal benchmark weight).
The overall rank is the average of the four individual ranks."""),

        code("""\
df['EDP'] = (df[COL_CPU_ENERGY] + df[COL_MEM_ENERGY]) * df[COL_TIME]  # J · s

# Two-step aggregation: benchmark-level mean → language-level mean (equal benchmark weight)
per_bench = df.groupby(['language', 'benchmark']).agg(
    paradigm    = ('paradigm', 'first'),
    cpu_mean_J  = (COL_CPU_ENERGY, 'mean'),
    mem_mean_J  = (COL_MEM_ENERGY, 'mean'),
    time_mean_s = (COL_TIME, 'mean'),
    edp_mean_Js = ('EDP', 'mean'),
)
agg = per_bench.groupby('language').agg(
    paradigm    = ('paradigm', 'first'),
    cpu_mean_J  = ('cpu_mean_J', 'mean'),
    mem_mean_J  = ('mem_mean_J', 'mean'),
    time_mean_s = ('time_mean_s', 'mean'),
    edp_mean_Js = ('edp_mean_Js', 'mean'),
).round(4)

agg['cpu_rank']  = agg['cpu_mean_J'].rank().astype(int)
agg['mem_rank']  = agg['mem_mean_J'].rank().astype(int)
agg['time_rank'] = agg['time_mean_s'].rank().astype(int)
agg['edp_rank']  = agg['edp_mean_Js'].rank().astype(int)
agg['overall_rank'] = (
    (agg['cpu_rank'] + agg['mem_rank'] + agg['time_rank'] + agg['edp_rank']) / 4
).round(2)

ranking = agg.sort_values('edp_rank')
ranking.index.name = 'Language'
ranking[['paradigm', 'cpu_mean_J', 'mem_mean_J', 'time_mean_s', 'edp_mean_Js',
         'cpu_rank', 'mem_rank', 'time_rank', 'edp_rank', 'overall_rank']]"""),

        code("""\
export = ranking[['paradigm', 'cpu_mean_J', 'mem_mean_J', 'time_mean_s',
                  'edp_mean_Js', 'cpu_rank', 'mem_rank', 'time_rank',
                  'edp_rank', 'overall_rank']].copy()
export.columns = ['Paradigm', 'CPU Energy (J)', 'Mem Energy (J)', 'Time (s)',
                  'EDP (J·s)', 'CPU Rank', 'Mem Rank', 'Time Rank', 'EDP Rank',
                  'Overall Rank']
export.to_csv(OUTPUTS_DIR / 'ranking_summary.csv')
print(f"Saved → {OUTPUTS_DIR / 'ranking_summary.csv'}")
export"""),

        md("""\
## 2. Normalized Efficiency Comparison

Each metric is expressed as a **ratio relative to the best (lowest) language** — so 1.0 = best
and e.g. 5.0 means this language consumes 5× more CPU energy / RAM energy / time than the
most efficient language. Values are computed from the **mean** across all 8 benchmarks,
matching the CLBG presentation style."""),

        code("""\
# Aggregate to per-(language × benchmark) means first, then average across benchmarks.
# This gives each benchmark equal weight regardless of how many runs survived outlier removal.
per_bench = df.groupby(['language', 'benchmark'])[[COL_CPU_ENERGY, COL_MEM_ENERGY, COL_TIME]].mean()
norm_agg  = per_bench.groupby('language').mean()

norm_agg['CPU Energy Normalized'] = (norm_agg[COL_CPU_ENERGY] / norm_agg[COL_CPU_ENERGY].min()).round(2)
norm_agg['RAM Energy Normalized'] = (norm_agg[COL_MEM_ENERGY] / norm_agg[COL_MEM_ENERGY].min()).round(2)
norm_agg['Time Normalized']       = (norm_agg[COL_TIME]        / norm_agg[COL_TIME].min()).round(2)

norm_ranking = (
    norm_agg[['CPU Energy Normalized', 'RAM Energy Normalized', 'Time Normalized']]
    .sort_values('CPU Energy Normalized')
    .reset_index()
    .rename(columns={'language': 'Language'})
)

norm_ranking.index = norm_ranking.index + 1  # rank starts at 1
norm_ranking.index.name = 'Rank'

norm_ranking"""),

        md("""\
## 3. Radar Chart — Paradigm Profile

One polygon per paradigm, with axes normalised to [0, 1] (0 = best, 1 = worst).
This reveals the energy/speed trade-off profile of each execution model."""),

        code("""\
paradigm_agg = df.groupby('paradigm').agg(
    cpu  = (COL_CPU_ENERGY, 'median'),
    mem  = (COL_MEM_ENERGY, 'median'),
    time = (COL_TIME, 'median'),
    edp  = ('EDP', 'median'),
)

norm = (paradigm_agg - paradigm_agg.min()) / (paradigm_agg.max() - paradigm_agg.min())

categories = ['CPU Energy (J)', 'Memory Energy (J)', 'Execution Time (s)', 'EDP (J·s)']
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
for paradigm in PARADIGM_ORDER:
    values = norm.loc[paradigm].tolist()
    values += values[:1]
    ax.plot(angles, values, color=PARADIGM_COLORS[paradigm], linewidth=2, label=paradigm)
    ax.fill(angles, values, color=PARADIGM_COLORS[paradigm], alpha=0.15)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylim(0, 1)
ax.set_title('Paradigm Profile (normalised; lower = better)', fontsize=13, pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'paradigm_radar.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 4. Normalised Metrics Heatmap

All four metrics normalised to [0, 1] per column. Lower values (greener) are better.
Enables direct visual comparison of language profiles across all metrics in human-readable units."""),

        code("""\
metrics = {
    'CPU Energy (J)': COL_CPU_ENERGY,
    'Mem Energy (J)': COL_MEM_ENERGY,
    'Time (s)':       COL_TIME,
    'EDP (J·s)':      'EDP',
}
norm_df = pd.DataFrame(index=ranking.index)
for label, col in metrics.items():
    vals = df.groupby('language')[col].median()
    norm_df[label] = (vals - vals.min()) / (vals.max() - vals.min())

norm_df = norm_df.loc[ranking.index]  # order by overall rank

fig, ax = plt.subplots(figsize=(9, 10))
sns.heatmap(norm_df, annot=True, fmt='.2f',
            cmap=sns.diverging_palette(120, 10, as_cmap=True),
            center=0.5, vmin=0, vmax=1, ax=ax,
            linewidths=0.5, cbar_kws={'label': '0 = best, 1 = worst'})
ax.set_title('Normalised Metric Heatmap (sorted by Overall Rank)', fontsize=12)
ax.set_ylabel('Language (best → worst overall)')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'normalised_heatmap.png', bbox_inches='tight')
plt.show()"""),

        md("""\
## 5. Top 3 / Bottom 3 per Metric

Quick-reference tables for the most and least efficient languages on each metric.
All values in human-readable units (J, s, J·s)."""),

        code("""\
metric_cols = {
    'CPU Energy (J)':    COL_CPU_ENERGY,
    'Memory Energy (J)': COL_MEM_ENERGY,
    'Execution Time (s)':COL_TIME,
    'EDP (J·s)':         'EDP',
}
units = {'CPU Energy (J)': 'J', 'Memory Energy (J)': 'J',
         'Execution Time (s)': 's', 'EDP (J·s)': 'J·s'}

for label, col in metric_cols.items():
    med_series = df.groupby('language')[col].median().sort_values()
    top3 = med_series.head(3)
    bot3 = med_series.tail(3)
    unit = units[label]
    print(f"\\n{'─'*55}")
    print(f"  {label}")
    print(f"  Top 3 (most efficient):")
    for lang, val in top3.items():
        print(f"    • {lang:12s} ({PARADIGM[lang]:12s})  {val:>10.3f} {unit}")
    print(f"  Bottom 3 (least efficient):")
    for lang, val in bot3.items():
        print(f"    • {lang:12s} ({PARADIGM[lang]:12s})  {val:>10.3f} {unit}")"""),

        md("""\
## 6. Key Findings

A bullet-point summary of the main findings in human-readable units (J, s, J·s),
suitable for direct citation in the thesis."""),

        code("""\
cpu_rank_ser  = df.groupby('language')[COL_CPU_ENERGY].median().sort_values()
time_rank_ser = df.groupby('language')[COL_TIME].median().sort_values()
edp_rank_ser  = df.groupby('language')['EDP'].median().sort_values()

aot_cpu  = df[df['paradigm']=='AOT'][COL_CPU_ENERGY].median()
jit_cpu  = df[df['paradigm']=='JIT'][COL_CPU_ENERGY].median()
int_cpu  = df[df['paradigm']=='Interpreted'][COL_CPU_ENERGY].median()
aot_time = df[df['paradigm']=='AOT'][COL_TIME].median()
jit_time = df[df['paradigm']=='JIT'][COL_TIME].median()
int_time = df[df['paradigm']=='Interpreted'][COL_TIME].median()

print(\"\"\"
KEY FINDINGS — Benchmark Energy & Time Analysis (18 languages, 8 CLBG benchmarks)
═════════════════════════════════════════════════════════════════════════════════\"\"\")

print(f\"\"\"
CPU ENERGY (unit: J)
  • Most efficient:   {', '.join(cpu_rank_ser.head(3).index)}
  • Least efficient:  {', '.join(cpu_rank_ser.tail(3).index)}
  • AOT median:       {aot_cpu:.2f} J
  • JIT median:       {jit_cpu:.2f} J  ({jit_cpu/aot_cpu:.1f}× AOT)
  • Interpreted med.: {int_cpu:.2f} J  ({int_cpu/aot_cpu:.1f}× AOT)

EXECUTION TIME (unit: s)
  • Fastest:          {', '.join(time_rank_ser.head(3).index)}
  • Slowest:          {', '.join(time_rank_ser.tail(3).index)}
  • AOT median:       {aot_time:.2f} s
  • JIT median:       {jit_time:.2f} s  ({jit_time/aot_time:.1f}× AOT)
  • Interpreted med.: {int_time:.2f} s  ({int_time/aot_time:.1f}× AOT)

ENERGY-DELAY PRODUCT (unit: J·s)
  • Best EDP:         {', '.join(edp_rank_ser.head(3).index)}
  • Worst EDP:        {', '.join(edp_rank_ser.tail(3).index)}
  • Best median EDP:  {edp_rank_ser.iloc[0]:.2f} J·s  ({edp_rank_ser.index[0]})
  • Worst median EDP: {edp_rank_ser.iloc[-1]:.2f} J·s ({edp_rank_ser.index[-1]})

Note: All values are medians across 8 CLBG benchmarks and ~10 runs per combination.
Use non-parametric tests (notebooks 02–03) when comparing paradigm distributions.
\"\"\")"""),
    ]
    save(n, "04_comparative_v2.ipynb")


# ── Run all ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    make_nb01()
    make_nb02()
    make_nb03()
    make_nb04()
    print("\nAll notebooks generated successfully.")
