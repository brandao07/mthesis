# C Benchmark Insights

**Language:** C  
**Compiler:** GCC 15.2.0 (via Docker image `gcc:15.2.0`)  
**Docker image:** `gcc:15.2.0` (standard upstream GCC image — same for all benchmarks)  
**Compilation model:** AOT — each benchmark is compiled in `setup-commands` and run as a native binary in the `flow`.  
**No `build_in_tmp.sh` scripts exist** — all compilation is performed directly in the YAML `setup-commands`.

---

## Per-Benchmark Breakdown

---

**binary-trees — C**

- **Execution:** AOT via `gcc 15.2.0` with `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp -I/usr/include/apr-1.0 -lapr-1`; runtime invocation: `/tmp/main 21`.
- **Concurrency:** Multi-threaded via OpenMP. `#pragma omp parallel` at `main.c:100` distributes tree-depth iterations across available threads; `#pragma omp single nowait` at `main.c:109` assigns long-lived-tree creation to one thread while others process other depths via `#pragma omp for nowait` at `main.c:119`. Thread count is controlled by OpenMP's runtime default (typically equals number of logical CPUs — scales with CPU count). Each thread gets its own APR memory pool (`thread_Memory_Pool`).
- **Build/runtime config:** `-O3` full optimization; `-fomit-frame-pointer` removes frame pointer for an extra register; `-march=native` enables all CPU-specific instructions available on the host; `-fopenmp` enables OpenMP threading; `-I/usr/include/apr-1.0 -lapr-1` links the Apache Portable Runtime (APR) pool allocator (installed via `apt-get install libapr1-dev` in setup). No GC — manual pool allocation via APR.
- **Source of flags:** `benchmarks/c/binary-trees.yml:11` (compile command); `benchmarks/c/binary-trees/main.c:100,109,119` (OpenMP pragmas); `benchmarks/c/binary-trees.yml:10` (apt-get install libapr1-dev).

---

**fannkuch-redux — C**

- **Execution:** AOT via `gcc 15.2.0` with `-pipe -Wall -O3 -fomit-frame-pointer -march=native -pthread`; runtime invocation: `/tmp/main 12`.
- **Concurrency:** Multi-threaded via POSIX threads (`pthreads`). `pthread_create` is called at `main.c:149` to spawn `nthreads - 1` worker threads, and the main thread also executes `fannkuch_func` directly. Default `nthreads = 4` (hardcoded at `main.c:116`); can be overridden via `-t <n>` CLI flag (max 64 threads — `MAX_THREADS` defined at `main.c:113`). Does NOT scale with CPU count automatically — fixed at 4 unless overridden. Atomic coordination via `__sync_fetch_and_add` (work-stealing block assignment) and `__sync_lock_test_and_set` (spin-lock for max_flips update).
- **Build/runtime config:** `-O3`; `-fomit-frame-pointer`; `-march=native`; `-pthread` links pthreads. Extensive SIMD: source includes `<smmintrin.h>` (SSE 4.1) at `main.c:18`; uses `__m128i` intrinsics for permutation arithmetic throughout `fannkuch_func`. No OpenMP.
- **Source of flags:** `benchmarks/c/fannkuch-redux.yml:9` (compile command); `benchmarks/c/fannkuch-redux/main.c:18` (SSE 4.1 include); `benchmarks/c/fannkuch-redux/main.c:113,116,148-151` (thread count and pthread_create).

---

**fasta — C**

- **Execution:** AOT via `gcc 15.2.0` with `-pipe -Wall -O3 -fomit-frame-pointer -march=native`; runtime invocation: `/tmp/main 25000000`.
- **Concurrency:** Single-threaded. No `pthread_create`, no OpenMP pragmas, no threading includes anywhere in `main.c`. Pure sequential execution.
- **Build/runtime config:** `-O3`; `-fomit-frame-pointer`; `-march=native`. No special math flags. Uses buffered `write(1, ...)` calls (POSIX write) for output. Lookup-table–based random FASTA generation (`build_hash` precomputes a 139968-entry character table at `main.c:136`). No extra libraries.
- **Source of flags:** `benchmarks/c/fasta.yml:9` (compile command); `benchmarks/c/fasta/main.c` (no threading constructs confirmed by inspection).

---

**k-nucleotide — C**

- **Execution:** AOT via `gcc 15.2.0` with `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp`; runtime invocation: `/tmp/main < /tmp/repo/inputs/fasta-25000000.txt` (stdin redirect, `shell: sh` required).
- **Concurrency:** Multi-threaded via OpenMP. `#pragma omp parallel sections` at `main.c:215` dispatches 7 independent tasks — 5 exact oligonucleotide count queries and 2 frequency-generation passes — each as a separate `#pragma omp section`. Thread count defaults to OpenMP runtime (scales with CPU count). Sections are data-independent (read-only shared `polynucleotide` array; each section writes to its own `output_Buffer[i]` slot).
- **Build/runtime config:** `-O3`; `-fomit-frame-pointer`; `-march=native`; `-fopenmp`. Uses bundled `khash.h` header-only hash table (`benchmarks/c/k-nucleotide/khash.h`); custom hash function `CUSTOM_HASH_FUNCTION` overrides default khash hash at `main.c:21`. No dynamic library installs needed beyond `libgomp` (bundled with GCC). No extra `-l` flags.
- **Source of flags:** `benchmarks/c/k-nucleotide.yml:9` (compile command); `benchmarks/c/k-nucleotide/main.c:215` (OpenMP parallel sections pragma).

---

**mandelbrot — C**

- **Execution:** AOT via `gcc 15.2.0` with `-pipe -Wall -O3 -fomit-frame-pointer -march=native -mno-fma -fno-finite-math-only -fopenmp`; runtime invocation: `/tmp/main 16000`.
- **Concurrency:** Multi-threaded via OpenMP. `#pragma omp parallel for schedule(guided)` at `main.c:167` and `main.c:181` parallelizes the outer row loop across all available threads. Thread count scales with OpenMP runtime default (CPU count). Two code paths based on `wid_ht % 64`: 8-pixel-per-iteration path at `main.c:167` and 64-pixel-per-iteration path at `main.c:181`; for input 16000 (divisible by 64) the 64-pixel path is used.
- **Build/runtime config:** `-O3`; `-fomit-frame-pointer`; `-march=native`; `-fopenmp`. `-mno-fma` disables fused multiply-add instructions despite `-march=native` potentially enabling them; `-fno-finite-math-only` ensures correct IEEE NaN/Inf handling (required for correctness). Explicit SSE2 SIMD: source includes `<emmintrin.h>` at `main.c:19`; uses `__m128d` double-pair vectors throughout. Source comment at `main.c:13` references `-ffast-math` in the original CLBG flags — this repo uses `-mno-fma -fno-finite-math-only` instead (notably **omits** `-ffast-math` and `-mfpmath=sse -msse3`), trading some floating-point speed for correctness guarantees.
- **Source of flags:** `benchmarks/c/mandelbrot.yml:9` (compile command); `benchmarks/c/mandelbrot/main.c:13` (original CLBG comment with differing flags); `benchmarks/c/mandelbrot/main.c:19` (SSE2 include); `benchmarks/c/mandelbrot/main.c:167,181` (OpenMP pragmas).

---

**n-body — C**

- **Execution:** AOT via `gcc 15.2.0` with `-pipe -Wall -O3 -fomit-frame-pointer -march=native`; runtime invocation: `/tmp/main 50000000`.
- **Concurrency:** Single-threaded. No threading primitives, no OpenMP pragmas anywhere in `main.c`. Sequential simulation of 5 bodies (Sun, Jupiter, Saturn, Uranus, Neptune).
- **Build/runtime config:** `-O3`; `-fomit-frame-pointer`; `-march=native`. No extra libraries. Extensive explicit AVX2 SIMD: source includes `<x86intrin.h>` at `main.c:10`; uses `__m256d` (4-wide double) vectors throughout `advance` and `energy` functions. Custom `_mm256_rsqrt_pd` at `main.c:21` approximates reciprocal square root using `_mm_rsqrt_ps` (float) then refines with Goldschmidt's algorithm to achieve < 1e-9 error. The 4th lane of each `__m256d` position/velocity vector is unused (bodies have 3D coordinates; the 4th element is zero/padding).
- **Source of flags:** `benchmarks/c/n-body.yml:9` (compile command); `benchmarks/c/n-body/main.c:10,21` (AVX2 intrinsics).

---

**regex-redux — C**

- **Execution:** AOT via `gcc 15.2.0` with `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp -lpcre2-8`; runtime invocation: `/tmp/main < /tmp/repo/inputs/fasta-25000000.txt` (stdin redirect, `shell: sh` required).
- **Concurrency:** Multi-threaded via OpenMP. `#pragma omp parallel` at `main.c:109` creates a thread team. `#pragma omp single` at `main.c:119` has one thread perform the initial input stripping (sequential dependency). `#pragma omp single nowait` at `main.c:129` has one thread run all 5 replacement passes serially. `#pragma omp for schedule(dynamic) ordered` at `main.c:173` distributes the 9 counting patterns across threads, with `#pragma omp ordered` at `main.c:199` ensuring ordered output. Thread count scales with OpenMP runtime default (CPU count). Each thread has its own `pcre2_match_context`, `pcre2_jit_stack`, and `pcre2_match_data` to avoid contention.
- **Build/runtime config:** `-O3`; `-fomit-frame-pointer`; `-march=native`; `-fopenmp`; `-lpcre2-8` links PCRE2. PCRE2's JIT is used explicitly: `pcre2_jit_compile(regex, PCRE2_JIT_COMPLETE)` at `main.c:34` and `pcre2_jit_match` at `main.c:38`. `pcre2.h` is bundled in `benchmarks/c/regex-redux/` (not installed via apt-get). **Discrepancy: flags.md notes `libpcre2-dev` is required, but the YAML has no `apt-get install` step** — PCRE2 is available in the `gcc:15.2.0` image or the header is bundled and the `.so` is present without an explicit install step.
- **Source of flags:** `benchmarks/c/regex-redux.yml:9` (compile command); `benchmarks/c/regex-redux/main.c:109,119,129,173,199` (OpenMP pragmas); `benchmarks/c/regex-redux/main.c:34,38` (PCRE2 JIT).

---

**spectral-norm — C**

- **Execution:** AOT via `gcc 15.2.0` with `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp -lm`; runtime invocation: `/tmp/main 5500`.
- **Concurrency:** Multi-threaded via OpenMP. `#pragma omp parallel for schedule(static)` at `main.c:78` (in `eval_A_times_u`) and `main.c:115` (in `eval_At_times_u`) parallelizes the outer loop over matrix rows in strides of 4. Thread count scales with OpenMP runtime default (CPU count). Static schedule used explicitly (`schedule(static)`) because each chunk performs equal work (noted in source comment at `main.c:77`).
- **Build/runtime config:** `-O3`; `-fomit-frame-pointer`; `-march=native`; `-fopenmp`; `-lm` links libm (for `sqrt`). Explicit AVX2 SIMD: source includes `<x86intrin.h>` at `main.c:11`; `eval_A` uses `__m128i` and `__m256d` (`main.c:14–23`); the `kernel` function operates on `__m256d[4]` tiles (`main.c:26`). Uses approximate reciprocal (`_mm_rcp_ps`) refined with Goldschmidt's algorithm for matrix element inversion (`main.c:47–56`). Arrays aligned to `sizeof(__m256d)` (32 bytes) for aligned AVX2 loads/stores (`main.c:158,159`).
- **Source of flags:** `benchmarks/c/spectral-norm.yml:9` (compile command); `benchmarks/c/spectral-norm/main.c:11,78,115` (x86intrin include and OpenMP pragmas).

---

**fibonacci — C** *(extra benchmark, not part of CLBG 8)*

- **Execution:** AOT via `gcc 15.2.0` with `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp`; runtime invocation: `/tmp/main` (no arguments; `n = 49` is hardcoded at `main.c:13`).
- **Concurrency:** Single-threaded. No threading constructs anywhere in `main.c`. Despite `-fopenmp` being passed at compile time, the source contains no OpenMP pragmas — the flag has no runtime effect.
- **Build/runtime config:** `-O3`; `-fomit-frame-pointer`; `-march=native`; `-fopenmp` (compiled in but unused). Naive recursive Fibonacci (`fibonacci(n-1) + fibonacci(n-2)`) with no memoization — deliberately compute-intensive for benchmarking purposes.
- **Source of flags:** `benchmarks/c/fib.yml:9` (compile command); `benchmarks/c/fibonacci/main.c` (no OpenMP pragmas confirmed by inspection).

---

## Discrepancy log

1. **regex-redux — missing `apt-get install libpcre2-dev`:** `docs/flags.md` notes that regex-redux "Requires `libpcre2-dev`", but `benchmarks/c/regex-redux.yml` has **no `apt-get install` step**. The header `pcre2.h` is bundled in `benchmarks/c/regex-redux/` and `-lpcre2-8` is linked directly. It is possible the `gcc:15.2.0` Docker image includes `libpcre2-8` as a shared library (without dev headers), making the bundled header sufficient for compilation. This should be verified against the actual image contents if results differ from expectations.

2. **mandelbrot — source suggests `-ffast-math`, YAML omits it:** The source comment at `main.c:13` documents the original CLBG compile flags as including `-ffast-math -mfpmath=sse -msse3`. The actual YAML (`mandelbrot.yml:9`) uses `-mno-fma -fno-finite-math-only` instead — explicitly counteracting the unsafe floating-point optimizations of `-ffast-math`. This is a deliberate adaptation, not an error, but it means performance differs from the upstream CLBG reference.

3. **fibonacci — `-fopenmp` passed but unused:** `fib.yml:9` compiles with `-fopenmp`, but `benchmarks/c/fibonacci/main.c` contains no OpenMP pragmas. The flag links `libgomp` and enables the OpenMP runtime with no functional effect. This is harmless but potentially misleading if the flag is assumed to indicate parallelism.

4. **k-nucleotide — flags.md does not mention `khash.h`:** `flags.md` notes "`khash.h` is bundled in benchmark dir", which is accurate. However, it omits that no `-I` flag is needed because GCC finds the header via implicit same-directory inclusion. Confirmed: `main.c` uses `#include "khash.h"` (relative path) at `main.c:15`, and the compile command passes no `-I` flag; this works because the source file and `khash.h` reside in the same directory passed to `gcc`.

---

## Summary table row(s)

Benchmarks differ in concurrency, so rows are split:

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| C | AOT (GCC 15.2.0) | `-O3 -fomit-frame-pointer -march=native` | Multi-threaded (OpenMP, scales with CPU count) | binary-trees, k-nucleotide, mandelbrot, regex-redux, spectral-norm |
| C | AOT (GCC 15.2.0) | `-O3 -fomit-frame-pointer -march=native -pthread` | Multi-threaded (pthreads, fixed 4 threads by default) | fannkuch-redux; SSE 4.1 SIMD intrinsics |
| C | AOT (GCC 15.2.0) | `-O3 -fomit-frame-pointer -march=native` | Single-threaded | fasta, n-body; n-body uses AVX2 SIMD intrinsics |
| C | AOT (GCC 15.2.0) | `-O3 -fomit-frame-pointer -march=native -fopenmp` (unused) | Single-threaded | fibonacci (extra benchmark; OpenMP flag compiled in but no pragmas in source) |
