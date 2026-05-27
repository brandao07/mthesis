# NodeJS Benchmark Insights

**Language:** NodeJS (JavaScript)
**Node version:** 25 (image `node:25-alpine3.21`)
**Engine:** V8 (TurboFan JIT + Ignition interpreter pipeline)
**Execution model:** JIT compilation via V8. Scripts start in the Ignition bytecode interpreter and are progressively optimized by TurboFan as hot paths are identified (warmup effect applies). No AOT step; no `--jitless` flag used. All benchmarks run cold — each GMT measurement is a fresh process, so there is no cross-run JIT warmup carryover.
**No `build_in_tmp.sh` found** in any NodeJS benchmark directory — no pre-compilation or npm install step is needed.

---

## Per-Benchmark Breakdown

> **Binary-Trees — NodeJS**
> - Execution: JIT via V8 (Node 25); no node runtime flags beyond the script path and problem-size argument.
> - Concurrency: **multi-threaded via `worker_threads`**. The main thread spawns one `Worker` per depth-level task (up to `(maxDepth − 4) / 2 + 1` workers for depth 21 → up to 9 workers). Workers are not pooled; each is created for a single task, sends one result via `parentPort.postMessage`, then exits. Worker count is proportional to the problem size, not to CPU count — does **not** scale with `os.cpus()`.
> - Build/runtime config: none (no node flags).
> - Source of flags: `benchmarks/nodejs/binary-trees.yml:15` (command); concurrency: `benchmarks/nodejs/binary-trees/main.js:8,51`

> **Fannkuch-Redux — NodeJS**
> - Execution: JIT via V8 (Node 25); no node runtime flags.
> - Concurrency: **multi-threaded via `worker_threads`**. `threadReduce` spawns exactly `os.cpus().length` persistent workers (a thread pool), then distributes 720 work chunks across them in a work-stealing loop — each worker signals `ready`, receives a chunk, returns a `result`, then requests the next chunk until all chunks are exhausted. Worker count scales directly with available CPU count.
> - Build/runtime config: none (no node flags).
> - Source of flags: `benchmarks/nodejs/fannkuch-redux.yml:15`; concurrency: `benchmarks/nodejs/fannkuch-redux/main.js:8-9,168-170`

> **Fasta — NodeJS**
> - Execution: JIT via V8 (Node 25); no node runtime flags.
> - Concurrency: **multi-threaded via `worker_threads`**. The `randomFasta` function spawns exactly **4 workers** (hardcoded `const cpus = 4`) using `SharedArrayBuffer` for zero-copy communication of random number arrays between the main thread and workers. The `repeatFasta` section (ALU repeat) runs synchronously on the main thread. Worker count is **fixed at 4** regardless of CPU count.
> - Build/runtime config: none (no node flags).
> - Source of flags: `benchmarks/nodejs/fasta.yml:15`; concurrency: `benchmarks/nodejs/fasta/main.js:9,91,98`

> **K-Nucleotide — NodeJS**
> - Execution: JIT via V8 (Node 25); no node runtime flags. Input is read from stdin via a pipe (`shell: sh` in YAML for redirect).
> - Concurrency: **multi-threaded via `worker_threads`**. The master function creates exactly **4 workers** (hardcoded `let jobs = 4` / `[...Array(jobs)].map(...)` ) . Worker 0 handles the sequence-to-buffer transformation and frequency computations for k=1 and k=2 plus 'ggt'; workers 1–3 each handle one or two longer k-mer lookups. After the full sequence is read, all 4 workers receive the shared sequence simultaneously for parallel analysis. Worker count is fixed at 4.
> - Build/runtime config: none (no node flags).
> - Source of flags: `benchmarks/nodejs/k-nucleotide.yml:16`; concurrency: `benchmarks/nodejs/k-nucleotide/main.js:11,105,145`

> **Mandelbrot — NodeJS**
> - Execution: JIT via V8 (Node 25); no node runtime flags.
> - Concurrency: **multi-threaded via `worker_threads`**. Spawns exactly `os.cpus().length` workers. A `SharedArrayBuffer` is used for the output pixel grid; workers self-schedule rows using `Atomics.compareExchange` on a shared atomic row counter (`nextY`), avoiding any explicit work distribution from the main thread. Worker count scales with CPU count.
> - Build/runtime config: none (no node flags).
> - Source of flags: `benchmarks/nodejs/mandelbrot.yml:15`; concurrency: `benchmarks/nodejs/mandelbrot/main.js:8-9,46-48`, atomics: `mandelbrot/main.js:86-87`

> **N-Body — NodeJS**
> - Execution: JIT via V8 (Node 25); no node runtime flags.
> - Concurrency: **single-threaded**. No `worker_threads`, `cluster`, or `child_process` import. The entire simulation — `offsetMomentum`, the main `advance` loop (50,000,000 iterations), and `energy` — runs sequentially on the event loop thread.
> - Build/runtime config: none (no node flags).
> - Source of flags: `benchmarks/nodejs/n-body.yml:15`; concurrency confirmed absent: `benchmarks/nodejs/n-body/main.js:1-164`

> **Regex-Redux — NodeJS**
> - Execution: JIT via V8 (Node 25); no node runtime flags. Input is read from stdin via a pipe (`shell: sh` in YAML for redirect); notably uses `fs.readFileSync('/dev/stdin', 'ascii')` rather than streaming.
> - Concurrency: **multi-threaded via `worker_threads`** — but only **1 worker** is spawned. The worker performs the 5-pass string replacement chain in parallel with the main thread, which concurrently runs the 9 regex match counts. Both tasks work on the same input string (passed by value as `workerData`). Effectively 2-way parallelism: main thread + 1 worker.
> - Build/runtime config: none (no node flags).
> - Source of flags: `benchmarks/nodejs/regex-redux.yml:16`; concurrency: `benchmarks/nodejs/regex-redux/main.js:12,40,53-58`

> **Spectral-Norm — NodeJS**
> - Execution: JIT via V8 (Node 25); no node runtime flags.
> - Concurrency: **multi-threaded via `worker_threads`**. Spawns exactly `os.cpus().length` persistent workers, each assigned a fixed row range (`[start, end)`) computed by dividing `n` into equal chunks. Workers receive work messages (`au`, `atu`) synchronously round-trip for each of 20 matrix-vector multiply steps (10 power iterations × 2 directions). A `SharedArrayBuffer` holds the `u`, `v`, `w` vectors for zero-copy access. Worker count scales with CPU count.
> - Build/runtime config: none (no node flags).
> - Source of flags: `benchmarks/nodejs/spectral-norm.yml:15`; concurrency: `benchmarks/nodejs/spectral-norm/main.js:9-10,53-55`

---

## Discrepancy log

- `docs/flags.md` Interpreted Languages table lists `NodeJS → node` with no flags noted — this is consistent with what the YMLs show (bare `node <script> <arg>`). However, the flags.md table gives no hint that NodeJS uses `worker_threads` for parallelism in 7 of 8 benchmarks; this is a documentation gap rather than a discrepancy in the actual files.
- Fasta uses a hardcoded `cpus = 4` (`fasta/main.js:91`) rather than `os.cpus().length`, which diverges from the other multi-threaded benchmarks (fannkuch-redux, mandelbrot, spectral-norm) that read `os.cpus().length` dynamically.
- Regex-redux spawns only 1 worker (a single background string-replace task) while the main thread handles regex counting — effectively 2 threads total, not a pool.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| NodeJS | JIT (V8 / TurboFan, with warmup) | none | Multi-threaded (`worker_threads`) for 7/8 benchmarks; single-threaded for n-body | Image: `node:25-alpine3.21`. Worker count: dynamic (`os.cpus().length`) for fannkuch-redux, mandelbrot, spectral-norm; fixed 4 for fasta and k-nucleotide; task-count-derived for binary-trees; 1 worker for regex-redux; 0 for n-body. SharedArrayBuffer used in fasta, mandelbrot, spectral-norm. No node runtime flags in any benchmark. |
