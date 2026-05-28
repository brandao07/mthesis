# Dart Benchmark Insights

**Language:** Dart  
**Dart SDK version:** 3.9.4  
**Docker image:** `dart:3.9.4-sdk` (confirmed in all 8 benchmark YAMLs)  
**Compilation type:** AOT — `dart compile exe` produces a self-contained native executable  
No extra compiler flags on any benchmark; the `dart compile exe` default optimization level is used throughout.

---

## Binary-Trees — Dart

- **Execution:** AOT via `dart compile exe` (Dart 3.9.4, image `dart:3.9.4-sdk`), no extra flags. Binary invoked as `/tmp/main 21`.
  - Source: `benchmarks/dart/binary-trees.yml:9`, `benchmarks/dart/binary-trees.yml:17`
- **Concurrency:** Multi-isolate, scales with CPU count. `nIsolates = Platform.numberOfProcessors` worker isolates are spawned via `Isolate.spawn(other, mainIsolate.sendPort)`. Workers pull tree-building tasks from a shared work queue managed by the main isolate via message passing. Each isolate processes one `RequestReply` (depth + iteration count) at a time and signals readiness for more.
  - Source: `benchmarks/dart/binary-trees/main.dart:11`, `main.dart:23-25`, `main.dart:57-70`
- **Build/runtime config:** No extra flags. `dart compile exe <src> -o /tmp/main`.
  - Source of flags: `benchmarks/dart/binary-trees.yml:9`

---

## Fannkuch-Redux — Dart

- **Execution:** AOT via `dart compile exe` (Dart 3.9.4, image `dart:3.9.4-sdk`), no extra flags. Binary invoked as `/tmp/main 12`.
  - Source: `benchmarks/dart/fannkuch-redux.yml:9`, `benchmarks/dart/fannkuch-redux.yml:17`
- **Concurrency:** Multi-isolate, scales with CPU count. `Platform.numberOfProcessors` worker isolates spawned via `Isolate.spawn(other, mainIsolate.sendPort)`. The permutation space is divided into 720 chunks; isolates pull `Request` objects from a queue and return `Int32List` results. Final max-flips and checksum are aggregated in the main isolate.
  - Source: `benchmarks/dart/fannkuch-redux/main.dart:133-135`, `main.dart:173-183`
- **Build/runtime config:** No extra flags. `dart compile exe <src> -o /tmp/main`.
  - Source of flags: `benchmarks/dart/fannkuch-redux.yml:9`

---

## Fasta — Dart

- **Execution:** AOT via `dart compile exe` (Dart 3.9.4, image `dart:3.9.4-sdk`), no extra flags. Binary invoked as `/tmp/main 25000000`.
  - Source: `benchmarks/dart/fasta.yml:9`, `benchmarks/dart/fasta.yml:17`
- **Concurrency:** Multi-isolate, fixed 2 isolates (not CPU-scaled). Two isolates are spawned with `Isolate.spawn`: `other` handles sequence ONE (repeated FASTA, writes directly to stdout), and `another` handles sequence TWO (weighted LCG, writes to stdout in order after a send/receive handshake). Sequence THREE is computed in the main isolate. Ordering is enforced via message passing.
  - Source: `benchmarks/dart/fasta/main.dart:96-125`, `main.dart:151-165`
- **Build/runtime config:** No extra flags. `dart compile exe <src> -o /tmp/main`.
  - Source of flags: `benchmarks/dart/fasta.yml:9`

---

## K-Nucleotide — Dart

- **Execution:** AOT via `dart compile exe` (Dart 3.9.4, image `dart:3.9.4-sdk`), no extra flags. Binary invoked as `/tmp/main < /tmp/repo/inputs/fasta-2500000.txt` (stdin redirect, `shell: sh`).
  - Source: `benchmarks/dart/k-nucleotide.yml:9`, `benchmarks/dart/k-nucleotide.yml:17-19`
- **Concurrency:** Multi-isolate, fixed 3 isolates (not CPU-scaled). Three calls to `par()` each spawn one isolate via `Isolate.spawn(findMultiple, ...)` to compute `find()` results for different k-mer groups (`['GGT','GGTA','GGTATT']`, `['GGTATTTTAATT']`, `['GGTATTTTAATTTATAGT']`) concurrently. `sort()` calls for lengths 1 and 2 run sequentially in the main isolate. Results are awaited via `Completer`-backed `RawReceivePort`.
  - Source: `benchmarks/dart/k-nucleotide/main.dart:144-154`, `main.dart:164-174`, `main.dart:156-162`
- **Build/runtime config:** No extra flags. `dart compile exe <src> -o /tmp/main`.
  - Source of flags: `benchmarks/dart/k-nucleotide.yml:9`

---

## Mandelbrot — Dart

- **Execution:** AOT via `dart compile exe` (Dart 3.9.4, image `dart:3.9.4-sdk`), no extra flags. Binary invoked as `/tmp/main 16000`.
  - Source: `benchmarks/dart/mandelbrot.yml:9`, `benchmarks/dart/mandelbrot.yml:17`
- **Concurrency:** Multi-isolate, fixed 4 isolates (not CPU-scaled, hardcoded segment count). The image rows are split into 4 weighted segments via `segments(h)` using hardcoded weights `[0.35, 0.5, 0.65]` (producing 4 ranges). Each segment is assigned to its own isolate via `Isolate.spawn(renderRows, ...)`. Isolates use `Isolate.exit(p, rows)` to return results and terminate. `Future.wait` collects all results before writing PBM output.
  - Source: `benchmarks/dart/mandelbrot/main.dart:18-27`, `main.dart:30-34`, `main.dart:109-120`
- **Build/runtime config:** No extra flags. `dart compile exe <src> -o /tmp/main`.
  - Source of flags: `benchmarks/dart/mandelbrot.yml:9`

---

## N-Body — Dart

- **Execution:** AOT via `dart compile exe` (Dart 3.9.4, image `dart:3.9.4-sdk`), no extra flags. Binary invoked as `/tmp/main 50000000`.
  - Source: `benchmarks/dart/n-body.yml:9`, `benchmarks/dart/n-body.yml:17`
- **Concurrency:** Single-isolate (single-threaded). No `Isolate.spawn` anywhere in the source. No `dart:isolate` import. Pure sequential simulation loop over 5 bodies for 50 million steps.
  - Source: `benchmarks/dart/n-body/main.dart:1-159` (no `dart:isolate` import; `main()` at line 150 is purely sequential)
- **Build/runtime config:** No extra flags. `dart compile exe <src> -o /tmp/main`.
  - Source of flags: `benchmarks/dart/n-body.yml:9`

---

## Regex-Redux — Dart

- **Execution:** AOT via `dart compile exe` (Dart 3.9.4, image `dart:3.9.4-sdk`), no extra flags. Binary invoked as `/tmp/main < /tmp/repo/inputs/fasta-5000000.txt` (stdin redirect, `shell: sh`).
  - Source: `benchmarks/dart/regex-redux.yml:9`, `benchmarks/dart/regex-redux.yml:17-19`
- **Concurrency:** Multi-isolate, fixed 1 isolate (not CPU-scaled). One isolate is spawned via `Isolate.spawn(magicReplacements, Data(z, mainIsolate.sendPort))` to perform the 5 sequential regex-replacement passes while the main isolate concurrently counts 9 pattern matches with `printPatternMatches(z)`. Results are combined via a single `ReceivePort` message.
  - Source: `benchmarks/dart/regex-redux/main.dart:17-28`, `main.dart:66-68`
- **Build/runtime config:** No extra flags. Uses Dart's built-in `RegExp` (no native PCRE2 binding).
  - Source of flags: `benchmarks/dart/regex-redux.yml:9`

---

## Spectral-Norm — Dart

- **Execution:** AOT via `dart compile exe` (Dart 3.9.4, image `dart:3.9.4-sdk`), no extra flags. Binary invoked as `/tmp/main 5500`.
  - Source: `benchmarks/dart/spectral-norm.yml:9`, `benchmarks/dart/spectral-norm.yml:17`
- **Concurrency:** Multi-isolate, scales with CPU count. `nIsolates = Platform.numberOfProcessors` worker isolates spawned via `Isolate.spawn(other, mainIsolate.sendPort)`. The matrix rows are split into `nIsolates` spans (`Span.initialize`); each iteration of the power method dispatches spans to isolates via `ports[next].send(each)` round-robin and awaits all via a `Future.wait` barrier. Each isolate computes `auFromTo` or `atuFromTo` on its row-slice and returns a `Span` with the result.
  - Source: `benchmarks/dart/spectral-norm/main.dart:83-108`, `main.dart:111-126`, `main.dart:130-144`, `main.dart:154-165`
- **Build/runtime config:** No extra flags. `dart compile exe <src> -o /tmp/main`.
  - Source of flags: `benchmarks/dart/spectral-norm.yml:9`

---

## Discrepancy log

- **flags.md states** "No extra flags" for Dart across the board. This is confirmed for all 8 benchmarks — every `setup-commands` entry is `dart compile exe <src> -o /tmp/main` with no additional flags.
- **flags.md does not document per-benchmark concurrency differences**, which are significant: 5 benchmarks use isolates (binary-trees, fannkuch-redux, fasta, k-nucleotide, mandelbrot, regex-redux, spectral-norm) and 1 is fully single-isolate (n-body). Additionally, the number of isolates varies: some scale with `Platform.numberOfProcessors` (binary-trees, fannkuch-redux, spectral-norm), some use a fixed count (fasta: 2, k-nucleotide: 3, mandelbrot: 4, regex-redux: 1). This is expected — flags.md only documents compiler flags, not concurrency — but worth noting for completeness.
- No actual flag discrepancies found between flags.md and the YAML files.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| Dart (binary-trees) | AOT (`dart compile exe`) | None | Multi-isolate; `Platform.numberOfProcessors` isolates, CPU-scaled | Worker-pool via message passing |
| Dart (fannkuch-redux) | AOT (`dart compile exe`) | None | Multi-isolate; `Platform.numberOfProcessors` isolates, CPU-scaled | 720 chunks distributed to workers |
| Dart (fasta) | AOT (`dart compile exe`) | None | Multi-isolate; 2 isolates, fixed | Ordered stdout via handshake protocol |
| Dart (k-nucleotide) | AOT (`dart compile exe`) | None | Multi-isolate; 3 isolates, fixed | One isolate per k-mer group; I/O on stdin |
| Dart (mandelbrot) | AOT (`dart compile exe`) | None | Multi-isolate; 4 isolates, fixed (weighted row segments) | `Isolate.exit()` for result return |
| Dart (n-body) | AOT (`dart compile exe`) | None | Single-isolate (no parallelism) | Pure sequential; no `dart:isolate` import |
| Dart (regex-redux) | AOT (`dart compile exe`) | None | Multi-isolate; 1 isolate (parallel with main) | Main counts matches; isolate does replacements; Dart built-in RegExp |
| Dart (spectral-norm) | AOT (`dart compile exe`) | None | Multi-isolate; `Platform.numberOfProcessors` isolates, CPU-scaled | Row-slice dispatch with round-robin + barrier sync |
