# Ruby Benchmark Insights

**Language:** Ruby  
**Version:** 3.4 (image `ruby:3.4`; `build_in_tmp.sh` probes `/opt/src/ruby-3.4.0/bin/ruby` first, falls back to system `ruby`)  
**Execution model:** JIT-compiled via Ruby's built-in YJIT compiler (`--yjit`). No separate compile step — `build_in_tmp.sh` generates a shell wrapper at `/tmp/ruby-<bench>` that embeds all flags at setup time.  
**Base runtime flags (all benchmarks):** `--yjit -W0`

- `--yjit`: enables Ruby's YJIT (Yet Another JIT) compiler, introduced in Ruby 3.1 and production-ready from 3.2+
- `-W0`: suppresses all runtime warnings

---

## Per-Benchmark Breakdown

> **Binary-Trees — Ruby**
> - **Execution:** JIT via `ruby --yjit -W0` (Ruby 3.4 from image `ruby:3.4`). No compilation step; wrapper generated at setup time by `build_in_tmp.sh`.
> - **Concurrency:** Multi-process. Uses the `MiniParallel` module (defined inline) which spawns worker processes via `Process.fork`. Worker count = `[array.size, core_count].min` where `core_count` reads `/proc/cpuinfo` processor entries. A pool of coordinator `Thread`s (one per worker process) dispatches work items through pipes using `Marshal.dump`/`Marshal.load`; each worker process handles serialised work items until EOF. Falls back to single-process sequential iteration when `core_count == 1`. Scales with CPU count.
> - **Build flags:** None (no compilation).
> - **Runtime flags:** `--yjit -W0` (from `build_in_tmp.sh` wrapper).
> - **Source:** `benchmarks/ruby/binary-trees/build_in_tmp.sh`, `benchmarks/ruby/binary-trees.yml`, `benchmarks/ruby/binary-trees/main.rb`.
> - **Notes:** Tree nodes represented as nested two-element arrays `[left, right]` (`nil` for leaves). GC behaviour depends on YJIT's default settings; no explicit GC tuning. Parallel path only activates when `core_count > 1`.

---

> **Fannkuch-Redux — Ruby**
> - **Execution:** JIT via `ruby --yjit -W0` (Ruby 3.4 from image `ruby:3.4`). No compilation step; wrapper generated at setup time by `build_in_tmp.sh`.
> - **Concurrency:** Multi-process. Same `MiniParallel` module as binary-trees. Worker count = `core_count` from `/proc/cpuinfo`. Permutation space is divided into weighted chunks (adjusted to even out workload across workers) assigned to `Process.fork`-ed worker processes. Threads in the parent coordinate dispatch via pipes and `Mutex`. A JRuby fallback path using `Thread.new` directly is present in the source (`RUBY_PLATFORM == 'java'` guard at line 198) but is never taken under MRI/YJIT. Falls back to single-process when `core_count == 1`. Scales with CPU count.
> - **Build flags:** None (no compilation).
> - **Runtime flags:** `--yjit -W0` (from `build_in_tmp.sh` wrapper).
> - **Source:** `benchmarks/ruby/fannkuch-redux/build_in_tmp.sh`, `benchmarks/ruby/fannkuch-redux.yml`, `benchmarks/ruby/fannkuch-redux/main.rb`.
> - **Notes:** Weighted chunk distribution attempts to equalise workload by shifting chunk boundaries based on an empirically derived weight table. The JRuby thread branch is dead code under MRI.

---

> **Fasta — Ruby**
> - **Execution:** JIT via `ruby --yjit -W0` (Ruby 3.4 from image `ruby:3.4`). No compilation step; wrapper generated at setup time by `build_in_tmp.sh`.
> - **Concurrency:** Single-process. No `Process.fork`, `Thread`, or other concurrency primitives in `main.rb`. Output is generated strictly sequentially.
> - **Build flags:** None (no compilation).
> - **Runtime flags:** `--yjit -W0` (from `build_in_tmp.sh` wrapper).
> - **Source:** `benchmarks/ruby/fasta/build_in_tmp.sh`, `benchmarks/ruby/fasta.yml`, `benchmarks/ruby/fasta/main.rb`.
> - **Notes:** Uses `instance_eval` to dynamically generate a `map_value` method with inlined conditional chain at construction time (`generate_map_value_method`), effectively specialising the lookup at startup. Output uses in-place string mutation (`setbyte`) to avoid allocations per row.

---

> **K-Nucleotide — Ruby**
> - **Execution:** JIT via `ruby --yjit -W0` (Ruby 3.4 from image `ruby:3.4`). No compilation step; wrapper generated at setup time by `build_in_tmp.sh`.
> - **Concurrency:** Multi-process. Uses a `Worker` class (defined inline) that calls `Process.fork` once per work item; worker count is fixed at 7 (2 frequency tasks from `FREQS = [1, 2]` + 5 nucleotide search tasks from `NUCLEOS`). Each child writes its result string to a pipe; parent collects results via `IO#read`. All 7 workers are spawned before any result is consumed, so they run concurrently. Worker count is fixed regardless of CPU count.
> - **Build flags:** None (no compilation).
> - **Runtime flags:** `--yjit -W0` (from `build_in_tmp.sh` wrapper).
> - **Source:** `benchmarks/ruby/k-nucleotide/build_in_tmp.sh`, `benchmarks/ruby/k-nucleotide.yml`, `benchmarks/ruby/k-nucleotide/main.rb`.
> - **Notes:** Input is read from `stdin` (`< /tmp/repo/inputs/fasta-2500000.txt`), requiring `shell: sh` in the YAML flow. The full sequence is loaded into the global `$seq` before forking, so all child processes inherit a copy of the data.

---

> **Mandelbrot — Ruby**
> - **Execution:** JIT via `ruby --yjit -W0` (Ruby 3.4 from image `ruby:3.4`). No compilation step; wrapper generated at setup time by `build_in_tmp.sh`.
> - **Concurrency:** Multi-process. Uses the same `MiniParallel` module as binary-trees and fannkuch-redux. Worker count = `core_count` from `/proc/cpuinfo`. Each worker process computes a subset of image rows; results (byte strings per row) are returned through pipes with `Marshal`. Coordinator threads in the parent drive dispatch. Falls back to single-process iteration when `core_count == 1`. Scales with CPU count.
> - **Build flags:** None (no compilation).
> - **Runtime flags:** `--yjit -W0` (from `build_in_tmp.sh` wrapper).
> - **Source:** `benchmarks/ruby/mandelbrot/build_in_tmp.sh`, `benchmarks/ruby/mandelbrot.yml`, `benchmarks/ruby/mandelbrot/main.rb`.
> - **Notes:** Output is a raw PBM bitmap stream (`P4` format). Row computation uses direct bitwise accumulation. `MiniParallel` distributes the full row array `(0...Size).to_a` across workers; results are joined in order after all workers finish.

---

> **N-Body — Ruby**
> - **Execution:** JIT via `ruby --yjit -W0` (Ruby 3.4 from image `ruby:3.4`). No compilation step; wrapper generated at setup time by `build_in_tmp.sh`.
> - **Concurrency:** Single-process. No `Process.fork`, `Thread`, or other concurrency primitives in `main.rb`. Pure sequential O(N²) simulation.
> - **Build flags:** None (no compilation).
> - **Runtime flags:** `--yjit -W0` (from `build_in_tmp.sh` wrapper).
> - **Source:** `benchmarks/ruby/n-body/build_in_tmp.sh`, `benchmarks/ruby/n-body.yml`, `benchmarks/ruby/n-body/main.rb`.
> - **Notes:** Models 5 bodies (Sun, Jupiter, Saturn, Uranus, Neptune). Uses standard Ruby `attr_accessor`-based `Planet` class with mutable velocity state. `Math.sqrt` is called per pairwise interaction.

---

> **Regex-Redux — Ruby**
> - **Execution:** JIT via `ruby --yjit -W0` (Ruby 3.4 from image `ruby:3.4`). No compilation step; wrapper generated at setup time by `build_in_tmp.sh`.
> - **Concurrency:** Multi-process with a Thread-based coordinator. `match_results` spawns 9 `Thread`s (one per matcher in `MATCHERS`). Each thread calls `pattern_count` which is aliased to `forked_pattern_count` on MRI (the alias is applied unconditionally for non-Java platforms at class load time). `forked_pattern_count` calls `Process.fork` to run the actual scan in a child process and reads the result back through a pipe. This produces 9 threads × 9 forked child processes running concurrently. Fixed at 9 workers; does not scale with CPU count. Input is read from `stdin` (`< /tmp/repo/inputs/fasta-5000000.txt`), requiring `shell: sh` in the YAML flow.
> - **Build flags:** None (no compilation).
> - **Runtime flags:** `--yjit -W0` (from `build_in_tmp.sh` wrapper).
> - **Source:** `benchmarks/ruby/regex-redux/build_in_tmp.sh`, `benchmarks/ruby/regex-redux.yml`, `benchmarks/ruby/regex-redux/main.rb`.
> - **Notes:** The `forked_pattern_count` method (lines 53–65) shadows `pattern_count` on MRI so that each regex scan runs in an isolated child process, avoiding GIL contention. The final substitution pass (`final_transform!`) runs in the parent process after all matchers complete.

---

> **Spectral-Norm — Ruby**
> - **Execution:** JIT via `ruby --yjit -W0` (Ruby 3.4 from image `ruby:3.4`). No compilation step; wrapper generated at setup time by `build_in_tmp.sh`.
> - **Concurrency:** Multi-process. Uses a `Worker` class (defined inline) that calls `Process.fork` for each worker. Worker count is hardcoded: `Worker.map` passes a default `worker_count = 6` (`main.rb:65`), capped to `[enum.size, worker_count].min`. Each worker owns a strided subset of the row indices (`index, step = total`). IPC via pipes: children write serialised `[idx, value]` pairs with `Marshal.dump`; parent uses `IO.select` to gather all results. Fixed at up to 6 workers; does not scale with CPU count.
> - **Build flags:** None (no compilation).
> - **Runtime flags:** `--yjit -W0` (from `build_in_tmp.sh` wrapper).
> - **Source:** `benchmarks/ruby/spectral-norm/build_in_tmp.sh`, `benchmarks/ruby/spectral-norm.yml`, `benchmarks/ruby/spectral-norm/main.rb`.
> - **Notes:** Runs 10 power iterations of the A·v and Aᵀ·v operations. Each full `eval_AtA_times_u` call invokes `Worker.map` twice (once for `eval_A_times_u`, once for `eval_At_times_u`), so 40 fork-wave rounds occur in total (10 iterations × 2 operations × 2 for u and v passes).

---

## Discrepancy Log

1. **flags.md does not document the `/opt/src/ruby-3.4.0/bin/ruby` probe.** All eight `build_in_tmp.sh` scripts check for a custom Ruby binary at `/opt/src/ruby-3.4.0/bin/ruby` before falling back to system `ruby`. `flags.md` describes the wrapper mechanism but does not mention this path probe. No functional impact if the custom binary is absent, but the exact version used could differ if that path exists in the container.

2. **flags.md says "no compilation step" but `build_in_tmp.sh` does copy the source file.** `flags.md` correctly characterises Ruby as having no compilation step. The `cp` of `main.rb` to `/tmp/ruby-<bench>.rb` inside `build_in_tmp.sh` is a file staging step, not compilation; the description is accurate. No discrepancy in substance.

3. **Spectral-norm worker count (6) is hardcoded, not CPU-derived — not mentioned in flags.md or YAML.** All other multi-process Ruby benchmarks (binary-trees, fannkuch-redux, mandelbrot) derive worker count from `/proc/cpuinfo`. Spectral-norm defaults to 6 workers regardless of the available CPU count. Neither `flags.md` nor any YAML comment documents this. If the container has fewer than 6 logical CPUs, `Worker.map` caps the count to `enum.size` (which is the matrix dimension `n=5500`), so in practice it always runs with 6 processes.

4. **K-nucleotide worker count (7) is fixed, not CPU-derived — not mentioned in flags.md.** `flags.md` documents only the runtime flags (`--yjit -W0`) and makes no mention of concurrency behaviour. The fixed-7-worker fork pattern is undocumented.

5. **Regex-redux: Thread+fork hybrid is undocumented.** `flags.md` does not note that regex-redux uses a two-layer concurrency model (9 Threads, each spawning a fork). This is materially different from the `MiniParallel` CPU-scaled fork pools used by other benchmarks.

---

## Summary Table Row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| Ruby (binary-trees) | JIT (YJIT) | `--yjit -W0` | Multi-process: `MiniParallel` `Process.fork` pool, CPU-scaled via `/proc/cpuinfo`; Thread-based work dispatch in parent | Falls back to single-process when `core_count == 1` |
| Ruby (fannkuch-redux) | JIT (YJIT) | `--yjit -W0` | Multi-process: `MiniParallel` `Process.fork` pool, CPU-scaled; weighted chunk distribution; JRuby Thread path is dead code under MRI | Falls back to single-process when `core_count == 1` |
| Ruby (fasta) | JIT (YJIT) | `--yjit -W0` | Single-process | Dynamic `map_value` method generated via `instance_eval` at startup |
| Ruby (k-nucleotide) | JIT (YJIT) | `--yjit -W0` | Multi-process: 7 fixed `Process.fork` workers (2 freq + 5 nucleotide); IPC via pipes | Fixed worker count; reads from stdin |
| Ruby (mandelbrot) | JIT (YJIT) | `--yjit -W0` | Multi-process: `MiniParallel` `Process.fork` pool, CPU-scaled; Thread-based work dispatch in parent | Falls back to single-process when `core_count == 1` |
| Ruby (n-body) | JIT (YJIT) | `--yjit -W0` | Single-process | Pure sequential O(N²) simulation; no concurrency |
| Ruby (regex-redux) | JIT (YJIT) | `--yjit -W0` | Multi-process + multi-threaded: 9 Threads each spawning one `Process.fork`; fixed 9 workers; IPC via pipes | Reads from stdin; fork-per-Thread hybrid not CPU-scaled |
| Ruby (spectral-norm) | JIT (YJIT) | `--yjit -W0` | Multi-process: 6 hardcoded `Process.fork` workers; strided row distribution; IPC via pipes with `IO.select` | Fixed at 6 workers regardless of CPU count |
