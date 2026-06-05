#!/usr/bin/env bash
# Generates large fasta input files used by k-nucleotide and regex-redux benchmarks.
# Requires gcc. Run from the repo root: bash scripts/generate_inputs.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUTS_DIR="$REPO_ROOT/inputs"
FASTA_SRC="$REPO_ROOT/benchmarks/c/fasta/main.c"
FASTA_BIN="$(mktemp /tmp/fasta-gen.XXXXXX)"

cleanup() { rm -f "$FASTA_BIN"; }
trap cleanup EXIT

echo "Compiling C fasta generator..."
gcc -pipe -O3 -fomit-frame-pointer "$FASTA_SRC" -o "$FASTA_BIN"

generate() {
    local n="$1"
    local out="$INPUTS_DIR/fasta-${n}.txt"
    if [[ -f "$out" ]]; then
        echo "  $out already exists, skipping."
        return
    fi
    echo "  Generating fasta-${n}.txt (n=$n)..."
    "$FASTA_BIN" "$n" > "$out"
    echo "  Done: $(du -h "$out" | cut -f1)  $out"
}

generate 25000000
