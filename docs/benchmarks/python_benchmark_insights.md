# Python Benchmark Insights

## Runtime: CPython 3.13 — Interpreted Bytecode VM

- **Image**: `python:3.13-slim` (all 8 benchmarks)
- **Runtime**: CPython 3.13, invoked as `python3`
- **JIT**: None used. CPython 3.13 ships an experimental JIT (enabled via `--enable-experimental-jit` at build time), but the standard `python:3.13-slim` image does not enable it. All execution is via the CPython bytecode interpreter.
- **Runtime flag**: `-OO` is passed on all benchmarks. This enables level-2 optimization: removes `assert` statements and strips docstrings from bytecodes. It does not affect algorithmic behavior.
- **No build step**: Source files are executed directly from the repository mount (`/tmp/repo/benchmarks/python/<benchmark>/main.py`). There is no compilation or pre-build phase in `setup-commands`.
- **GIL**: CPython 3.13 retains the GIL by default. All threading-based concurrency would be GIL-constrained. To work around this, all multi-threaded benchmarks use `multiprocessing` (separate OS processes with independent GILs) rather than `threading`.

---

## Per-Benchmark Breakdown

> **Binary-Trees — Python**
> - Execution: Interpreted via `python3 -OO` (CPython 3.13 from image `python:3.13-slim`). No compilation step.
> - Concurrency: Multi-process via `multiprocessing.Pool`. The code checks `mp.cpu_count() > 1` at runtime: if more than one CPU is available, it creates a `Pool()` (default worker count = `cpu_count()`) and uses `pool.map(make_check, ...)` to distribute tree-building and checking tasks across worker processes. Falls back to serial `map()` on single-CPU hosts. Scales with the available CPU count at runtime.
> - Runtime flags: `-OO` (remove assert statements and docstrings)
> - Source: `benchmarks/python/binary-trees/main.py`, `benchmarks/python/binary-trees.yml`
> - Notes: The `mp.Pool()` call with no argument uses `os.cpu_count()` processes. Worker count is not pinned and will vary with the host environment. The GIL is irrelevant here: each worker process is an independent Python interpreter.

> **Fannkuch-Redux — Python**
> - Execution: Interpreted via `python3 -OO` (CPython 3.13 from image `python:3.13-slim`). No compilation step.
> - Concurrency: Multi-process via `multiprocessing.Pool`. Splits the full permutation space into `cpu_count()` tasks (falling back to 1 task if `task_size < 20000`). Each task is an independent range of permutations. Uses `pool.starmap(task, task_args)` to distribute work. The split is adaptive: if the problem is small enough that each partition would be under 20000 items, it collapses to a single-process run.
> - Runtime flags: `-OO` (remove assert statements and docstrings)
> - Source: `benchmarks/python/fannkuch-redux/main.py`, `benchmarks/python/fannkuch-redux.yml`
> - Notes: Worker count equals `cpu_count()` dynamically. The pool uses `with Pool() as pool:` context manager (no explicit `processes` argument). Concurrency scales with CPU count, subject to the minimum task-size guard.

> **Fasta — Python**
> - Execution: Interpreted via `python3 -OO` (CPython 3.13 from image `python:3.13-slim`). No compilation step.
> - Concurrency: Multi-process via `multiprocessing.Process` (not Pool). Three tasks are created: `copy_from_sequence`, `random_selection` (IUB), `random_selection` (homosapiens). When `cpu_count() >= 2`, each task runs in a separate `Process` with a chain of `Lock` objects to enforce output ordering (task 1 must write before task 2, task 2 must write before task 3). The `random_selection` path also internally spawns additional sub-processes (one per `cpu_count() * 3` partition) for the lookup-and-write phase when input is large enough. When `cpu_count() < 2`, all three tasks execute sequentially in the main process.
> - Runtime flags: `-OO` (remove assert statements and docstrings)
> - Source: `benchmarks/python/fasta/main.py`, `benchmarks/python/fasta.yml`
> - Notes: This benchmark has a two-level parallelism design: top-level 3-process pipeline parallelism plus intra-task sub-process parallelism for random sequence generation. The lock chain (`pre_lock`/`post_lock` pairs) guarantees stdout ordering across processes. All parallelism is `multiprocessing`-based (bypasses GIL).

> **K-Nucleotide — Python**
> - Execution: Interpreted via `python3 -OO` (CPython 3.13 from image `python:3.13-slim`). No compilation step.
> - Concurrency: Multi-process via `multiprocessing.Pool`. Partitions the input sequence into `n = cpu_count()` equal slices when `len(sequence) > 128 * cpu_count()`, otherwise runs single-process. Uses `pool.starmap_async(lean_call(count_frequencies), lean_jobs)` to distribute frequency counting across workers. A `lean_buffer` global dict avoids re-serializing the large sequence across process boundaries by using a shared-memory key lookup pattern.
> - Runtime flags: `-OO` (remove assert statements and docstrings). Input is read from stdin (`< /tmp/repo/inputs/fasta-25000000.txt`), requiring `shell: sh` in the flow.
> - Source: `benchmarks/python/k-nucleotide/main.py`, `benchmarks/python/k-nucleotide.yml`
> - Notes: The `lean_buffer` / `lean_call` pattern is a workaround for multiprocessing's pickle-based IPC: the large byte-sequence is stored in a module-level dict by integer key, and only the key is passed to workers. Workers look up the sequence from this shared dict (which is copied into each subprocess on fork on Linux). Worker count equals `cpu_count()`.

> **Mandelbrot — Python**
> - Execution: Interpreted via `python3 -OO` (CPython 3.13 from image `python:3.13-slim`). No compilation step.
> - Concurrency: Multi-process via `multiprocessing.Pool`. When `cpu_count() >= 2`, a `Pool()` is created and `pool.imap_unordered(compute_row, row_jobs)` distributes one row-computation job per pixel row. Results arrive out-of-order and are re-ordered via the `ordered_rows()` buffering generator before writing. When `cpu_count() < 2`, rows are computed sequentially with `map()`. Worker count is `cpu_count()` (default pool size).
> - Runtime flags: `-OO` (remove assert statements and docstrings)
> - Source: `benchmarks/python/mandelbrot/main.py`, `benchmarks/python/mandelbrot.yml`
> - Notes: `imap_unordered` provides backpressure-aware streaming from the pool; the `ordered_rows` function handles reordering in a bounded buffer of size `n`. Pool import is deferred inside the conditional branch (`from multiprocessing import Pool` only executed on multi-CPU hosts).

> **N-Body — Python**
> - Execution: Interpreted via `python3 -OO` (CPython 3.13 from image `python:3.13-slim`). No compilation step.
> - Concurrency: Single-threaded. The entire simulation runs in the main process as a sequential `advance()` loop over 50,000,000 steps. No `threading`, `multiprocessing`, or async constructs are present anywhere in the source.
> - Runtime flags: `-OO` (remove assert statements and docstrings)
> - Source: `benchmarks/python/n-body/main.py`, `benchmarks/python/n-body.yml`
> - Notes: Pure algorithmic workload — the lack of parallelism here is by design; the benchmark measures CPU-bound arithmetic throughput on a fixed 5-body system. The only import is `sys`.

> **Regex-Redux — Python**
> - Execution: Interpreted via `python3 -OO` (CPython 3.13 from image `python:3.13-slim`). No compilation step.
> - Concurrency: Multi-process via `multiprocessing.Process`. Spawns one worker process per available CPU (`cpu_count() or 1`). A manager-process/worker-process communication pattern using `multiprocessing.Pipe` and `multiprocessing.connection.wait` distributes the 9 counting tasks across workers and one serial replacement task to worker 0. Workers use PCRE2 via `ctypes` (not Python's `re` module) and call `pcre2_jit_compile_8` on each pattern to enable PCRE2's own JIT for matching.
> - Runtime flags: `-OO` (remove assert statements and docstrings). Input is read from stdin (`< /tmp/repo/inputs/fasta-25000000.txt`), requiring `shell: sh` in the flow. Requires `libpcre2-8-0` installed via `apt-get` in `setup-commands`.
> - Source: `benchmarks/python/regex-redux/main.py`, `benchmarks/python/regex-redux.yml`
> - Notes: This benchmark does not use Python's built-in `re` module at all — PCRE2 is loaded directly via `ctypes.CDLL(find_library("pcre2-8"))`. PCRE2's JIT (`pcre2_jit_compile_8`) runs within the C library; the Python interpreter itself remains unaffected. Shared memory (`RawArray`) is used for the sequences buffer to avoid copying it to each subprocess. Worker count is pinned to `cpu_count()`.

> **Spectral-Norm — Python**
> - Execution: Interpreted via `python3 -OO` (CPython 3.13 from image `python:3.13-slim`). No compilation step.
> - Concurrency: Multi-process via `multiprocessing.Pool` with exactly 4 worker processes (hardcoded: `Pool(processes=4)`). The pool is created in the `if __name__ == '__main__':` block and passed implicitly to the `multiply_AtAv` function via the module-level `pool` variable. Each `multiply_AtAv` call uses `pool.starmap(A_sum, ...)` and `pool.starmap(At_sum, ...)` to distribute matrix-vector operations across the 4 workers.
> - Runtime flags: `-OO` (remove assert statements and docstrings)
> - Source: `benchmarks/python/spectral-norm/main.py`, `benchmarks/python/spectral-norm.yml`
> - Notes: Unlike the other multiprocessing benchmarks, worker count is fixed at 4 regardless of `cpu_count()`. The `pool` object is used as a global within `multiply_AtAv` — it is created before `main()` is called and referenced as a free variable inside the function. This is the only benchmark with a hardcoded parallelism degree.

---

## Discrepancy log

**1. Regex-redux: input file differs between production YAML and cluster-scenario YAML.**

- `benchmarks/python/regex-redux.yml` (production): `< /tmp/repo/inputs/fasta-25000000.txt`
- `benchmarks/python/gmt-cluster-scenario.yml` (regex-redux flow): `< /tmp/repo/inputs/fasta-25000000.txt`

The cluster scenario uses half the input size compared to the standalone production YAML. This is inconsistent — the other per-benchmark YAMLs (binary-trees, fasta, etc.) use the same input sizes in both contexts.

**2. `docs/flags.md` description is incomplete for Python.**

`docs/flags.md` lists Python under "Interpreted Languages" with the note "No compilation step. The runtime is invoked directly in the GMT flow." This is accurate as far as it goes, but omits:
- The `-OO` optimization flag passed to `python3` on all benchmarks (strips asserts and docstrings).
- The `libpcre2-8-0` `apt-get` install in the regex-redux `setup-commands`.

The `-OO` flag is not a minor detail — it changes runtime behavior (removed asserts in source like those in `fannkuch-redux/main.py`) and is consistently applied across all benchmarks. It should be documented.

**3. Spectral-norm: hardcoded pool size of 4 does not adapt to CPU count.**

Every other multiprocessing benchmark uses `cpu_count()` to determine worker count. Spectral-norm hardcodes `Pool(processes=4)`. This is not a YAML/source discrepancy but is a notable behavioral difference from all other Python benchmarks in this suite.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| Python (binary-trees) | Interpreted; CPython 3.13 bytecode VM | `-OO` | Multi-process (`multiprocessing.Pool`, `cpu_count()` workers) | Workers scale with CPU count; GIL bypassed via separate processes |
| Python (fannkuch-redux) | Interpreted; CPython 3.13 bytecode VM | `-OO` | Multi-process (`multiprocessing.Pool`, `cpu_count()` workers) | Collapses to single-process if task size < 20000 |
| Python (fasta) | Interpreted; CPython 3.13 bytecode VM | `-OO` | Multi-process (`multiprocessing.Process`, 3 pipeline processes + intra-task sub-processes) | Two-level parallelism; lock chain enforces output ordering |
| Python (k-nucleotide) | Interpreted; CPython 3.13 bytecode VM | `-OO` | Multi-process (`multiprocessing.Pool`, `cpu_count()` workers) | `lean_buffer` avoids re-pickling large sequence; collapses to single-process for small inputs |
| Python (mandelbrot) | Interpreted; CPython 3.13 bytecode VM | `-OO` | Multi-process (`multiprocessing.Pool`, `cpu_count()` workers, `imap_unordered`) | Out-of-order row computation with ordered-output buffering |
| Python (n-body) | Interpreted; CPython 3.13 bytecode VM | `-OO` | Single-threaded | Entirely sequential; no parallelism |
| Python (regex-redux) | Interpreted; CPython 3.13 bytecode VM | `-OO` | Multi-process (`multiprocessing.Process`, `cpu_count()` workers) | PCRE2 via `ctypes` (not Python `re`); PCRE2 JIT enabled per-pattern; shared memory for sequences |
| Python (spectral-norm) | Interpreted; CPython 3.13 bytecode VM | `-OO` | Multi-process (`multiprocessing.Pool`, 4 workers hardcoded) | Only benchmark with a fixed parallelism degree; pool is module-level global |
