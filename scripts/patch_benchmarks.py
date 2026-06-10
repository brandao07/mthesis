"""
Replace regex-redux and k-nucleotide rows in the source measurement files with
new data from kwa/results/update/, then regenerate results/results_linux.csv.

The clean base for each source file is read from git HEAD (not the working tree),
and rows are spliced as raw text lines. Untouched rows are therefore preserved
byte-for-byte, so the only diff in each source file is the swapped
regex-redux/k-nucleotide rows. Re-running is idempotent: it always rebuilds from
the committed base plus the update data.

All update-file and source-file headers are identical, so update rows can be
spliced in verbatim without any column re-ordering or CSV re-serialization.
"""

import csv
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
RESULTS_DIR = REPO_ROOT / "kwa" / "results"
UPDATE_DIR = RESULTS_DIR / "update"
BENCHMARKS_TO_REPLACE = {"regex-redux", "k-nucleotide"}


def split_lines(text: str) -> list[str]:
    # Split CSV text into lines, dropping a single trailing-newline empty element.
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def field_indices(header: str) -> tuple[int, int]:
    # Return (language_index, benchmark_index) parsed from a CSV header line.
    cols = next(csv.reader([header]))
    return cols.index("language"), cols.index("benchmark")


def benchmark_of(raw_line: str, idx: int) -> str:
    # Extract the benchmark field from a raw CSV data line.
    return next(csv.reader([raw_line]))[idx]


def head_text(rel_path: str) -> str:
    # Return the committed (HEAD) content of a tracked file.
    return subprocess.run(
        ["git", "show", f"HEAD:{rel_path}"],
        capture_output=True, text=True, check=True,
    ).stdout


def collect_update_rows() -> dict[str, list[str]]:
    # Gather raw rr/kn data lines from every update CSV, keyed by language.
    by_lang: dict[str, list[str]] = {}
    for f in sorted(UPDATE_DIR.glob("*.csv")):
        lines = split_lines(f.read_text())
        li, bi = field_indices(lines[0])
        for raw in lines[1:]:
            fields = next(csv.reader([raw]))
            if fields[bi] in BENCHMARKS_TO_REPLACE:
                by_lang.setdefault(fields[li], []).append(raw)
    return by_lang


def patch_file(source: Path, new_rows: list[str]) -> tuple[int, int]:
    # Rebuild a source file from its HEAD base: keep non-rr/kn rows verbatim,
    # drop old rr/kn rows, append the new rr/kn rows. Returns (removed, added).
    rel = source.relative_to(REPO_ROOT).as_posix()
    lines = split_lines(head_text(rel))
    header = lines[0]
    _, bi = field_indices(header)

    kept, removed = [], 0
    for raw in lines[1:]:
        if benchmark_of(raw, bi) in BENCHMARKS_TO_REPLACE:
            removed += 1
        else:
            kept.append(raw)

    out_lines = [header] + kept + new_rows
    source.write_text("\n".join(out_lines) + "\n")
    return removed, len(new_rows)


def main() -> None:
    by_lang = collect_update_rows()
    print(f"Update data covers {len(by_lang)} languages: {', '.join(sorted(by_lang))}\n")

    for lang in sorted(by_lang):
        source = RESULTS_DIR / f"measurements_{lang}.csv"
        if not source.exists():
            print(f"  {lang}: source file not found, skipping")
            continue
        removed, added = patch_file(source, by_lang[lang])
        print(f"  {lang}: removed {removed} rows, added {added} rows → {source.name}")

    print("\nRunning merge_results.py...")
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    python = str(venv_python) if venv_python.exists() else sys.executable
    result = subprocess.run(
        [python, str(REPO_ROOT / "scripts" / "merge_results.py")],
        check=True, capture_output=True, text=True,
    )
    print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)


if __name__ == "__main__":
    main()
