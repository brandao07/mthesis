# Perl Benchmark Insights

**Language:** Perl  
**Version:** 5.42.1 (threaded build)  
**Docker image:** `perl:5.42.1-threaded`  
**Execution model:** Interpreted — Perl compiles source to an internal opcode tree at startup, then interprets it. There is **no JIT compiler**. The image variant is the **threaded** build of Perl, which is required for Perl `ithreads` (`use threads`) to function.  
**No compilation step** in any benchmark: `perl` is invoked directly in the GMT flow without a `setup-commands` block.

---

## Per-Benchmark Breakdown

> **binary-trees — Perl**
> - Execution: interpreted via `perl 5.42.1` (no JIT); invoked as `perl /tmp/repo/benchmarks/perl/binary-trees/main.pl 21`
> - Concurrency: **multi-threaded — Perl ithreads**. Uses `use threads` and `use threads::shared` (lines 8–14 of `main.pl`). Worker count: reads `/proc/cpuinfo` at runtime via `num_cpus()` (lines 38–45) and creates `$cpu_count - 1` worker threads (line 69: `for ( 1 .. $cpu_count - 1)`); the main thread also participates (line 91: `depth_iteration()`). Total active threads = cpu_count. **Scales with CPU count.**
> - Build/runtime config: no flags passed to `perl`; no CPAN modules installed (only core `threads` and `threads::shared`); no `setup-commands` in YAML.
> - Source of flags: `benchmarks/perl/binary-trees.yml:15` (command), `benchmarks/perl/binary-trees/main.pl:8-14` (thread usage), `main.pl:38-45,63,69` (cpu count and thread spawn)

---

> **fannkuch-redux — Perl**
> - Execution: interpreted via `perl 5.42.1` (no JIT); invoked as `perl /tmp/repo/benchmarks/perl/fannkuch-redux/main.pl 12`
> - Concurrency: **multi-threaded — Perl ithreads**. Uses `use threads` (line 7 of `main.pl`). Spawns exactly `$n` threads (one per starting permutation, where `$n` = the input argument = 12): the main loop (lines 74–79) calls `threads->create(\&fannkuchredux, ...)` `$count` (= `$n`) times. Thread count is **fixed to the input value (12), not CPU count**.
> - Build/runtime config: no flags passed to `perl`; no CPAN modules; no `setup-commands` in YAML.
> - Source of flags: `benchmarks/perl/fannkuch-redux.yml:15` (command), `benchmarks/perl/fannkuch-redux/main.pl:7` (thread usage), `main.pl:74-79` (thread spawn loop)

---

> **fasta — Perl**
> - Execution: interpreted via `perl 5.42.1` (no JIT); invoked as `perl /tmp/repo/benchmarks/perl/fasta/main.pl 25000000`
> - Concurrency: **single-threaded**. No `use threads`, `fork`, or any parallelism construct in `main.pl`. Uses `eval` to generate and compile code strings at runtime for the random FASTA generation inner loop (lines 71–86) — this is a runtime code-generation optimisation, not concurrency.
> - Build/runtime config: no flags passed to `perl`; no CPAN modules; no `setup-commands` in YAML. Uses `use strict`, `use warnings`, `use feature 'say'` (lines 8–10) — all part of Perl core.
> - Source of flags: `benchmarks/perl/fasta.yml:15` (command), `benchmarks/perl/fasta/main.pl:8-10` (no threads import), `main.pl:71-86` (eval-based code generation)

---

> **k-nucleotide — Perl**
> - Execution: interpreted via `perl 5.42.1` (no JIT); invoked as `perl /tmp/repo/benchmarks/perl/k-nucleotide/main.pl 0 < /tmp/repo/inputs/fasta-25000000.txt` (stdin redirect requires `shell: sh`, set at `k-nucleotide.yml:15-16`)
> - Concurrency: **multi-threaded — Perl ithreads**. Uses `use threads` (line 11 of `main.pl`). Thread count is determined by `num_cpus()` (lines 60–65), stored in `$threads` (line 13). For each frame length (1, 2, and each query string), `update_hash_for_frame()` spawns `$threads` worker threads (lines 37–50 of `update_hash_for_frame`) that each process a slice of the sequence. **Scales with CPU count.**
> - Build/runtime config: no flags passed to `perl`; no CPAN modules; no `setup-commands` in YAML.
> - Source of flags: `benchmarks/perl/k-nucleotide.yml:15-16` (command + shell), `benchmarks/perl/k-nucleotide/main.pl:11,13` (thread usage and count), `main.pl:37-50,60-65` (thread spawn and cpu detection)

---

> **mandelbrot — Perl**
> - Execution: interpreted via `perl 5.42.1` (no JIT); invoked as `perl /tmp/repo/benchmarks/perl/mandelbrot/main.pl 16000`
> - Concurrency: **multi-threaded — Perl ithreads**. Uses `use threads` and `use threads::shared` (lines 7–8 of `main.pl`). Thread count read from `/proc/cpuinfo` via `num_cpus()` (lines 51–58); creates exactly `num_cpus()` worker threads (line 66: `for (1 .. num_cpus())`). Workers pull row indices from a shared `@jobs` array in a work-stealing fashion (`process_queue`, lines 45–49). **Scales with CPU count.**
> - Build/runtime config: no flags passed to `perl`; no CPAN modules; no `setup-commands` in YAML.
> - Source of flags: `benchmarks/perl/mandelbrot.yml:15` (command), `benchmarks/perl/mandelbrot/main.pl:7-8` (thread usage), `main.pl:51-58,66` (cpu detection and thread spawn)

---

> **n-body — Perl**
> - Execution: interpreted via `perl 5.42.1` (no JIT); invoked as `perl /tmp/repo/benchmarks/perl/n-body/main.pl 50000000`
> - Concurrency: **single-threaded**. No `use threads`, `fork`, or any concurrency construct in `main.pl`. The program uses a `BEGIN` block with `eval` to generate and compile the `energy`, `advance`, and `offset_momentum` subroutines at startup (lines 20–138) with loop-unrolled, constant-indexed array accesses — this is a compile-time code-generation optimisation for performance, not parallelism.
> - Build/runtime config: no flags passed to `perl`; no CPAN modules; no `setup-commands` in YAML. Uses `use constant` (lines 10–12) from Perl core.
> - Source of flags: `benchmarks/perl/n-body.yml:15` (command), `benchmarks/perl/n-body/main.pl` (no threads import anywhere), `main.pl:20-138` (BEGIN/eval code-generation technique)

---

> **regex-redux — Perl**
> - Execution: interpreted via `perl 5.42.1` (no JIT); invoked as `perl /tmp/repo/benchmarks/perl/regex-redux/main.pl 0 < /tmp/repo/inputs/fasta-25000000.txt` (stdin redirect requires `shell: sh`, set at `regex-redux.yml:15-16`)
> - Concurrency: **hybrid — fork + Perl ithreads**. Uses `use threads` (line 14 of `main.pl`) and `fork` (line 67). The process forks once (line 67): the **child** spawns `ceil(9/3)` = **3 ithreads** (lines 73–80; `ITEMS_PER_THREAD = 3`, 9 variants / 3 = 3 threads) to count regex matches in parallel, then writes results to a pipe; the **parent** performs the IUB substitutions sequentially while the child works, then reads the child's results from the pipe. Total worker threads (inside child): **3 fixed ithreads**. The fork itself adds 1 additional OS-level process. Thread and fork counts are **fixed**, not CPU-dependent.
> - Build/runtime config: no flags passed to `perl`; no CPAN modules (uses only built-in `threads` and POSIX `fork`/`pipe`); no `setup-commands` in YAML.
> - Source of flags: `benchmarks/perl/regex-redux.yml:15-16` (command + shell), `benchmarks/perl/regex-redux/main.pl:14` (thread usage), `main.pl:16` (`ITEMS_PER_THREAD = 3`), `main.pl:67` (fork), `main.pl:73-80` (thread spawn in child)

---

> **spectral-norm — Perl**
> - Execution: interpreted via `perl 5.42.1` (no JIT); invoked as `perl /tmp/repo/benchmarks/perl/spectral-norm/main.pl 5500`
> - Concurrency: **multi-threaded — Perl ithreads**. Uses `use threads` (line 9 of `main.pl`). Thread count read from `/proc/cpuinfo` via `num_cpus()` (lines 82–89), stored in `$cpus` (line 11). Both `multiplyAv` (lines 42–59) and `multiplyAtv` (lines 61–79) partition the work into chunks of size `ceil(n / $cpus)` and each spawn `$cpus` threads per call. **Scales with CPU count.**
> - Build/runtime config: no flags passed to `perl`; no CPAN modules; no `setup-commands` in YAML.
> - Source of flags: `benchmarks/perl/spectral-norm.yml:15` (command), `benchmarks/perl/spectral-norm/main.pl:9,11` (thread usage and cpu count), `main.pl:42-59,61-79,82-89` (thread spawn and cpu detection)

---

## Discrepancy log

1. **`docs/flags.md` — Perl row is incomplete.** The Interpreted Languages table (`flags.md:234`) lists Perl runtime as simply `perl` with no flags and no further detail. This is accurate for the lack of flags but omits all concurrency information. Specifically: 6 of 8 benchmarks use Perl ithreads (`use threads`); regex-redux additionally uses `fork`; and fasta and n-body are the only single-threaded benchmarks. The flags.md table has no column for concurrency and no note about the threaded image variant (`perl:5.42.1-threaded`), which is architecturally significant because the threaded Perl build is required for `use threads` to work.

2. **fannkuch-redux thread count is input-bound, not CPU-bound.** Spawns `$n` = 12 threads (the input parameter), which on a system with fewer cores will oversubscribe the CPU. This is different from all other multi-threaded Perl benchmarks which read `/proc/cpuinfo`.

3. **regex-redux uses both `fork` and `threads` — the only benchmark with this hybrid model.** No discrepancy with files, but this is not documented anywhere and is architecturally distinct from the other benchmarks' thread-only model.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| Perl (binary-trees) | Interpreted (opcode tree, no JIT) | None | Multi-threaded: Perl ithreads; `num_cpus()` threads; scales with CPU | `perl:5.42.1-threaded`; `use threads` + `use threads::shared` |
| Perl (fannkuch-redux) | Interpreted (opcode tree, no JIT) | None | Multi-threaded: Perl ithreads; **12 fixed threads** (= input N); does not scale with CPU | `perl:5.42.1-threaded`; oversubscribes if CPU < 12 |
| Perl (fasta) | Interpreted (opcode tree, no JIT) | None | **Single-threaded** | `perl:5.42.1-threaded`; uses `eval`-based code generation for inner loop |
| Perl (k-nucleotide) | Interpreted (opcode tree, no JIT) | None | Multi-threaded: Perl ithreads; `num_cpus()` threads per frame; scales with CPU | `perl:5.42.1-threaded`; `use threads` |
| Perl (mandelbrot) | Interpreted (opcode tree, no JIT) | None | Multi-threaded: Perl ithreads; `num_cpus()` threads; scales with CPU; work-stealing queue | `perl:5.42.1-threaded`; `use threads` + `use threads::shared` |
| Perl (n-body) | Interpreted (opcode tree, no JIT) | None | **Single-threaded** | `perl:5.42.1-threaded`; uses `BEGIN`/`eval` loop-unrolling code generation |
| Perl (regex-redux) | Interpreted (opcode tree, no JIT) | None | **Hybrid: 1 fork + 3 fixed ithreads in child** | `perl:5.42.1-threaded`; parent does substitutions; child does regex matching in 3 threads; counts fixed, not CPU-scaled |
| Perl (spectral-norm) | Interpreted (opcode tree, no JIT) | None | Multi-threaded: Perl ithreads; `num_cpus()` threads per matrix-vector multiply; scales with CPU | `perl:5.42.1-threaded`; `use threads` |
