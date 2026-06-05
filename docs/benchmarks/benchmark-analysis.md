# Benchmark Analysis: Cross-Language Characterization

| Compilation Type | Languages |
|-----------------|-----------|
| AOT | C, C++, C#, Dart, Go, Haskell, Java, OCaml, Rust, Swift |
| JIT | Erlang, F#, Node.js, PHP, Ruby |
| Interpreted | Lua, Perl, Python |

---

## 1. Introduction

This document provides a cross-language characterization of the 8 Computer Language
Benchmarks Game (CLBG) benchmarks as implemented across the 18 languages in this thesis.
Its purpose is to support interpretation of energy efficiency measurement results by
documenting compilation strategies, enabling flags, concurrency models, and
implementation-level differences that materially affect energy and wall-clock outcomes.

The 8 benchmarks covered are: **binary-trees**, **fannkuch-redux**, **fasta**,
**k-nucleotide**, **mandelbrot**, **n-body**, **regex-redux**, and **spectral-norm**.

This file synthesizes the per-language detail found in the individual
`*_benchmark_insights.md` files in this directory. Those files contain full per-benchmark
breakdowns, flag-by-flag rationale, and source-code references. This document should be
read alongside them, not instead of them.

---

## 2. Summary Characterization Table

| Language | Compilation Type | Runtime/Compiler Version | Enabling Flags | Concurrency Model | CPU-Scaled? | Notes |
|----------|-----------------|--------------------------|----------------|-------------------|-------------|-------|
| C | AOT (GCC) | GCC 15.2.0 | `-O3 -fomit-frame-pointer -march=native` | OpenMP (most benchmarks); pthreads (fannkuch-redux); single-threaded (fasta, n-body) | Yes (OpenMP defaults to all CPUs) | fannkuch-redux hardcoded 4 pthreads; n-body uses AVX2 SIMD; mandelbrot uses `-mno-fma` |
| C++ | AOT (g++) | GCC 15.2.0 | `-O3 -fomit-frame-pointer -march=native -std=c++17` (most) | Varies per benchmark: TBB parallel STL, OpenMP, std::thread, std::async | Mixed | spectral-norm has no `-std` flag; binary-trees uses `-std=gnu++17` and TBB; fasta capped at 2 threads; n-body single-threaded with hard-coded AVX2 |
| C# | NativeAOT (dotnet publish) | .NET 9.0 | `OptimizationPreference=Speed, IlcInstructionSet=native, ServerGarbageCollection=true, ConcurrentGarbageCollection=true` | Varies: Task.Run, new Thread, ThreadPool, Parallel.For, PLINQ | Mixed | No CLR JIT warmup; binary-trees/fannkuch-redux fixed at 4 threads; most others CPU-scaled; n-body single-threaded; regex-redux uses PCRE2 via P/Invoke |
| Dart | AOT (dart compile exe) | Dart SDK 3.9.4 | None (default optimization) | Dart Isolates via Isolate.spawn + message passing | Mixed | binary-trees/fannkuch-redux/spectral-norm scale with Platform.numberOfProcessors; fasta=2, k-nucleotide=3, mandelbrot=4 isolates fixed; n-body single-isolate |
| Erlang | erlc → BEAM bytecode → BeamAsm JIT | OTP 29.0.0 | `-smp enable` at runtime; no extra erlc flags | Erlang lightweight processes via spawn/rpc:pmap/spawn_link | Yes (BEAM SMP schedulers use all logical CPUs) | BeamAsm JIT active (OTP ≥ 24); HiPE `-compile([native])` directives in 2 sources are no-ops under OTP 29; spectral-norm uniquely queries `logical_processors` |
| F# | JIT (CLR, dotnet build, NOT AOT) | .NET 9.0 | `AllowUnsafeBlocks=true, ServerGarbageCollection=true, ConcurrentGarbageCollection=true` | Varies: Async.Parallel, Parallel.For, Task.Run | Mixed | CLR JIT warmup cost on every run; output is a shell wrapper calling `dotnet <dll>`; n-body single-threaded with explicit AVX2 intrinsics |
| Go | AOT (go build) | Go 1.25 | None (toolchain default) | Goroutines scheduled by Go runtime | Mixed | fannkuch-redux hardcoded GOMAXPROCS=4; mandelbrot/spectral-norm use 2×NumCPU; regex-redux is the only CGO benchmark (libpcre via go-pcre) |
| Haskell | AOT (GHC + LLVM backend) | GHC 9.10.1 | `-O2 -XBangPatterns -fllvm -threaded -rtsopts` | GHC parallel RTS (`+RTS -N4`) with forkIO/par/rpar | No (all benchmarks fixed at 4 RTS threads) | n-body single-threaded despite `-N4`; mandelbrot uses `DoubleX2#` SIMD primops; binary-trees uses `Control.Parallel.Strategies` |
| Java | AOT (GraalVM native-image) | GraalVM CE 23.0.2 | `-O3 -march=native --gc=G1` (most); no `--gc` for binary-trees | Varies: ExecutorService, Thread[] with AtomicInteger work-stealing, producer–consumer | Yes (scales with availableProcessors()) | No JVM JIT warmup; G1 GC with serial fallback; regex-redux uses jextract + Panama Foreign API + PCRE2 JIT; k-nucleotide links fastutil-8.3.1.jar |
| Lua | luac bytecode pre-compile + PUC Lua 5.5 interpreter | PUC Lua 5.5 | None | Single-threaded (most); multi-process via io.popen (binary-trees=4, mandelbrot=6) | No (fixed process counts) | No JIT; luac pre-compiles source before timed flow; regex-redux uses lrexlib-pcre2 with PCRE2 JIT for the regex engine |
| NodeJS | JIT (V8/TurboFan) | Node.js 25 | None | worker_threads (7/8 benchmarks); single-threaded for n-body | Mixed | V8 JIT warmup applies; fasta/k-nucleotide fixed at 4 workers; mandelbrot/fannkuch-redux/spectral-norm scale with os.cpus().length; regex-redux uses only 1 worker |
| OCaml | AOT (ocamlopt native) | OCaml 5.4 | `-noassert -unsafe -O3 -inline 100 -ccopt -march=native` | Unix fork (most benchmarks); single-threaded (fasta, n-body, spectral-norm) | No (fixed fork counts) | Uses no Domains or Threads; fan-out sizes: k-nucleotide=7, binary-trees=varies by depth, fankkuch-redux=32, mandelbrot=64; regex-redux=2; uses pure-OCaml `re` library not PCRE2 |
| Perl | Interpreted (opcode tree, no JIT) | Perl 5.42.1 (threaded build) | None | Perl ithreads (use threads) or fork+ithreads (regex-redux) | Mixed | fasta/n-body single-threaded; binary-trees/k-nucleotide/mandelbrot/spectral-norm scale with `/proc/cpuinfo`; fannkuch-redux fixed at 12 threads (= input N) |
| PHP | JIT (OPcache JIT, 64M buffer) with interpreted fallback | PHP 8.4 | `-dzend_extension=opcache.so -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n` | pcntl_fork multi-process with shmop/sysvmsg/pipe IPC | Mixed | fasta/n-body single-process; fannkuch-redux/mandelbrot=2×CPU forks; k-nucleotide=6 fixed; regex-redux=4 fixed; spectral-norm=1×CPU forks |
| Python | Interpreted (CPython bytecode, no JIT) | CPython 3.13 | `-OO` | multiprocessing (separate OS processes, bypasses GIL) | Mixed | No JIT; spectral-norm hardcoded at 4 workers; n-body single-threaded; regex-redux uses PCRE2 via ctypes (not Python re module) |
| Ruby | JIT (YJIT) | Ruby 3.4 | `--yjit -W0` | Process.fork (MiniParallel CPU-scaled or fixed Worker class) | Mixed | YJIT warmup applies; fasta/n-body single-process; k-nucleotide=7 fixed forks; spectral-norm=6 fixed forks; regex-redux=9 Thread+fork hybrid |
| Rust | AOT (cargo/rustc) | Rust 1.93 | `-C opt-level=3 -C target-cpu=native -C codegen-units=1` (most) | rayon work-stealing (most); std::thread (fasta); tokio-threadpool (k-nucleotide) | Yes (rayon defaults to all logical CPUs) | n-body single-threaded with explicit AVX/AVX2 intrinsics (no Cargo); binary-trees/fannkuch-redux use `target-cpu=ivybridge` not `native` |
| Swift | AOT (swiftc) | Swift 6.0.3 | `-Ounchecked -wmo` | Grand Central Dispatch (GCD): DispatchQueue, concurrentPerform, DispatchGroup | Yes (GCD pool scales with CPUs) | n-body single-threaded; mandelbrot uses SIMD8<Double>; n-body uses SIMD4<Double>; regex-redux uses NSRegularExpression/ICU not PCRE2 |

---

## 3. Cross-Benchmark Patterns (by Benchmark)

### binary-trees

The binary-trees benchmark is multi-threaded in nearly all 18 languages, with the dominant
pattern being a parallel fan-out over tree-depth levels. Most languages scale worker count
to available CPU cores: C (OpenMP), C++ (C++17 parallel STL backed by TBB), Java
(ExecutorService), Rust (rayon), Go (goroutines), Python (multiprocessing.Pool), Ruby
(MiniParallel fork), Dart (CPU-scaled isolates), Erlang (rpc:pmap), F# (Async.Parallel),
C# (Task.Run), NodeJS (worker_threads), Perl (ithreads from /proc/cpuinfo), and Swift
(GCD) all parallelize the depth-iteration work. A subset uses fixed parallelism regardless
of host CPU count: Haskell fixes 4 RTS threads via `+RTS -N4`, OCaml's child count is
bounded by the depth range (not explicitly CPU-scaled), and Lua spawns exactly 4 child
processes via `io.popen`. The benchmark creates heavy allocation pressure from
short-lived tree nodes, so GC strategy is a material factor: C# and F# benefit from
Server GC, C uses an APR arena allocator, and Rust uses the bumpalo crate.

### fannkuch-redux

Fannkuch-redux is universally parallel, with every language distributing permutation chunks
across workers. The majority scale to CPU count: C++ (OpenMP), Java (Thread[] with
AtomicInteger work-stealing), PHP (2×CPU forks), NodeJS (os.cpus().length workers), Ruby
(MiniParallel fork with weighted chunks), Python (multiprocessing.Pool), F# (Async.Parallel
with ProcessorCount tasks), Erlang (spawn per chunk), and Swift (DispatchQueue.concurrentPerform).
Notable fixed-count outliers: C uses pthreads hardcoded to 4, C# uses 4 threads, Haskell
uses 4 forkIO workers with MVar synchronization, Go hardcodes GOMAXPROCS=4, OCaml
re-execs itself as 32 subprocesses via `Unix.open_process_in`, and Perl spawns exactly
12 ithreads matching the input argument N (which oversubscribes on machines with fewer
than 12 logical CPUs). Several languages use SIMD in the inner permutation loop: C (SSE 4.1
intrinsics), C++ (SSE2/SSSE3 with `_mm_shuffle_epi8`), Rust (SSE3+SSE4.1 intrinsics), and
C# (Vector128 with SIMD byte-level shuffles).

### fasta

Fasta exhibits the widest variation in concurrency strategy across the 18 languages.
Single-threaded implementations: C (sequential with a 139968-entry precomputed table),
OCaml, Lua, PHP, and Python (all single-process). Producer–consumer pipelines: C++ (2
threads with spinlock), Java (producer–consumer with ArrayBlockingQueue, nCPU−1 workers),
Swift (GCD P/C/W pipeline with semaphore coordination), F# (Task.Run per block), and C#
(ThreadPool.QueueUserWorkItem). Go uses a goroutine pipeline with a channel of futures.
Dart uses 2 fixed isolates with a send/receive handshake for output ordering. Haskell
uses 4 forkIO workers pinned to the 4-thread RTS. Rust and NodeJS both cap threads at
2 (Rust via `min(num_cpus, 2)`, NodeJS via hardcoded `cpus = 4`). Ruby is single-process.
A key challenge across all parallel implementations is preserving output ordering while
computing sections in parallel — every implementation uses some form of synchronization
(locks, semaphores, message passing, or join) to guarantee correct interleaving.

### k-nucleotide

K-nucleotide is multi-threaded or multi-process in the majority of languages, typically
parallelizing 7 independent frequency-counting tasks (2 frequency tables + 5 exact
oligonucleotide counts). CPU-scaled implementations: C (OpenMP sections), Java
(ExecutorService), Go (NumCPU goroutines with strided partition), Rust (tokio-threadpool
with 7 futures), Python (multiprocessing.Pool), Erlang (7 spawn workers), F# (Async.Parallel
with sub-task parallelism), C# (Task.Run + Parallel.ForEach), and Perl (ithreads per CPU
per frame). Fixed-count implementations: Ruby (7 fixed forks), OCaml (7 fork children),
Swift (8 tasks hardcoded), Dart (3 isolates), NodeJS (4 hardcoded workers). Haskell uses
64 parallel sparks consumed by 4 OS threads. A recurring challenge is the large input
sequence (2.5 MB FASTA file read from stdin): languages using fork-based parallelism
(OCaml, Ruby, PHP) copy the sequence into child processes via fork inheritance or pipe
serialization, which adds memory and IPC overhead.

### mandelbrot

Mandelbrot is the most uniformly parallel benchmark across all 18 languages — every
implementation except OCaml spectral-norm runs with multiple threads or processes.
The vast majority scale to available CPU count or use a 2× oversubscription: C (OpenMP
guided schedule), C++ (std::thread per hardware_concurrency), Java (2×availableProcessors),
Go (2×NumCPU), Rust (rayon par_chunks_mut), Python (multiprocessing.Pool, imap_unordered),
Dart (4 fixed isolates), Erlang (1 process per row — 16000 processes at N=16000),
F# (Parallel.For), C# (Parallel.For), NodeJS (os.cpus().length workers via Atomics),
Perl (ithreads work-stealing queue), PHP (2×CPU forks), and Swift (DispatchQueue.concurrentPerform).
Haskell uses 4 threads via `fork#` with an MVar work queue. Erlang's approach is the most
extreme: it spawns one process per image row (16001 processes for N=16000), relying on the
BEAM's lightweight process scheduler rather than explicit thread pooling. Several languages
apply SIMD at the pixel computation level: C (SSE2), C++ (AVX-512/AVX/SSE adaptive
dispatch), C# (Vector512<double> with 8-wide AVX-512), Haskell (`DoubleX2#` primops),
and Swift (SIMD8<Double>).

### n-body

N-body is uniquely single-threaded in all 18 languages — there is no independent work to
parallelize in the sequential 5-body simulation loop. Despite the single-threaded execution,
several languages employ explicit SIMD to vectorize the O(N²) pairwise force computation:
C (AVX2 with custom Goldschmidt rsqrt), C++ (hard-coded AVX2 with recursive template
loop-unrolling), C# (AVX2 Vector256<double> with unsafe pointer arithmetic), F# (explicit
AVX2 Avx.Multiply/Add intrinsics), Rust (extensive AVX/AVX2 intrinsic coverage with
custom Newton-Raphson rsqrt), and Swift (SIMD4<Double> with inline dot product). Languages
without explicit SIMD rely on compiler auto-vectorization (Go, Java, OCaml) or their
interpreter/JIT (Python, Ruby, Perl, Lua, NodeJS, PHP). Haskell nominally runs with
`+RTS -N4` but the source has no parallelism primitives; the `-threaded` flag adds
GHC parallel RTS overhead (GC synchronization, capability scheduling) with no
computational benefit — a subtle energy cost to be aware of when interpreting results.

### regex-redux

Regex-redux shows the most material cross-language implementation differences in the
benchmark suite. The most significant divergence is the regex engine: C, C++, Java, Go,
Haskell, Python, and Rust all use PCRE2 with its own JIT compiler (`pcre2_jit_compile`),
while F# and C# use the .NET managed `Regex` class with `RegexOptions.Compiled` (which
JIT-compiles regex patterns to .NET IL), Erlang uses the BEAM's built-in `re` module,
Lua uses lrexlib-pcre2 (PCRE2 Lua bindings), OCaml uses the pure-OCaml `re` library
with PCRE-compatible syntax but no C PCRE2 dependency, and Swift uniquely uses
`NSRegularExpression` backed by the ICU regex engine (part of Foundation on Linux).
The ICU engine has different performance characteristics from PCRE2's JIT, making Swift
regex-redux algorithmically non-equivalent to the PCRE2-using implementations. Concurrency
patterns for the parallel counting task are broadly similar: most languages launch 9
concurrent workers (one per variant pattern) and run the sequential substitution chain
independently; the key difference is whether they are OS threads, goroutines, Erlang
processes, isolates, or forked processes.

### spectral-norm

Spectral-norm is parallel in 15 of 18 languages, with the matrix-vector product rows
distributing cleanly to workers. CPU-scaled implementations: C (OpenMP static schedule),
C++ (OpenMP via `sched_getaffinity` CPU affinity count), Java (Thread[] partitioned by
row), Go (goroutines, 2×NumCPU via `GOMAXPROCS(runtime.NumCPU()*2)`), Rust (rayon
par_iter_mut), Python (multiprocessing.Pool, though hardcoded to 4 workers), Erlang
(spawn per `logical_processors`), C# (Parallel.For), NodeJS (os.cpus().length workers
with SharedArrayBuffer), F# (Parallel.For), Perl (ithreads per CPU), PHP (1×CPU forks
with Unix socket pipe-based barrier sync), and Swift (DispatchQueue.concurrentPerform).
Single-threaded or fixed-count outliers: OCaml runs single-threaded (no Domains or
Threads used), Haskell uses 4 forkIO threads with a CyclicBarrier (adaptive to numCapabilities),
Ruby hardcodes 6 fork workers, and Dart uses CPU-scaled isolates. SIMD appears in
several language implementations: C (AVX2 with aligned loads and approximate reciprocal),
Rust (SSE2+SSE3 F64x2 struct), C++ (SSE2 with emmintrin.h), C# (SSE2+SSE3 Vector128),
and F# (SSE4.1 with runtime availability guard).

---

## 4. Combined Discrepancy Log

The following discrepancies were identified between `docs/flags.md` (or YAML files) and
actual source/build behavior. Grouped by language. Languages with no discrepancies are
omitted.

### C

1. **regex-redux — missing `apt-get install libpcre2-dev`:** `docs/flags.md` notes that
   regex-redux requires `libpcre2-dev`, but `benchmarks/c/regex-redux.yml` has no
   `apt-get install` step. The header `pcre2.h` is bundled in the benchmark directory
   and `-lpcre2-8` is linked directly. The `gcc:15.2.0` image appears to provide the
   shared library without an explicit install step.

2. **mandelbrot — source suggests `-ffast-math`, YAML omits it:** The source comment at
   `main.c:13` documents the original CLBG compile flags as including `-ffast-math
   -mfpmath=sse -msse3`. The actual YAML uses `-mno-fma -fno-finite-math-only` instead —
   a deliberate adaptation for correctness guarantees, but it means performance differs
   from the upstream CLBG reference.

3. **fibonacci (extra benchmark) — `-fopenmp` compiled in but unused:** `fib.yml`
   compiles with `-fopenmp`, but the source contains no OpenMP pragmas. The flag links
   `libgomp` with no runtime effect.

4. **k-nucleotide — `khash.h` found via implicit relative path:** `main.c` uses
   `#include "khash.h"` with no `-I` flag; GCC resolves it because source and header
   share the same compilation directory. Not a bug, but not documented in flags.md.

### C++

1. **`flags.md` claims all benchmarks install `libboost-dev`:** False. Only binary-trees,
   fasta, and regex-redux install `libboost-dev`. Fannkuch-redux, k-nucleotide, mandelbrot,
   n-body, and spectral-norm have no `apt-get install` step and do not use Boost headers.

2. **spectral-norm compiled without `-std` flag:** The only C++ benchmark with no explicit
   C++ standard flag; all others use `-std=c++17` (or `-std=gnu++17` for binary-trees).

3. **mandelbrot uses `-pthread` vs `-lpthread` used by fasta and k-nucleotide:**
   Semantically equivalent on GCC but not the same flag string.

4. **binary-trees uses `-std=gnu++17` while all other C++ benchmarks use `-std=c++17`.**

5. **fasta hard-caps threads at `NUM_THREADS = 2`:** Not mentioned in `flags.md`; thread
   count does not scale with CPU count regardless of host hardware.

6. **regex-redux — `libpcre2-8` present in image without explicit install:** Setup-commands
   only install `libboost-dev`. The PCRE2 shared library appears to be bundled in the base
   `gcc:15.2.0` image.

### C#

1. **`flags.md` states "all benchmarks use identical project settings":** The k-nucleotide
   benchmark adds a `Microsoft.Experimental.Collections` NuGet package reference
   (`DictionarySlim<TKey,TValue>`) via a conditional block in `build_common.sh:68–74`.
   This per-benchmark override is not reflected in the flags.md summary.

### Erlang

1. **Source-level `-compile([native, {hipe, [o3]}])` directives not documented in
   flags.md:** Present in `fannkuchredux.erl` and `regexredux.erl`. Under OTP 29, HiPE
   was removed in OTP 26, so these directives are silently ignored; BeamAsm JIT applies
   instead.

2. **`spectralnorm.erl` carries `-compile([inline, {inline_size, 1000}])` not mentioned
   in flags.md:** This is a genuine compile-time optimization (aggressive inlining up to
   size 1000) honored by `erlc` at compile time.

3. **flags.md does not mention `-noshell` (all benchmarks) or `-noinput` (regex-redux
   only):** These runtime flags are part of actual invocations but absent from
   documentation.

### F#

1. **`fasta.yml` and `mandelbrot.yml` omit `setup_dependencies.sh`:** All other 6 F#
   benchmarks call `setup_dependencies.sh` (which pre-restores the NuGet package cache),
   but fasta and mandelbrot do not. Neither uses `Microsoft.Experimental.Collections`,
   so the omission is harmless but unexplained and inconsistent.

2. **flags.md describes the output launcher as "native" when it is a shell script:**
   `build_common.sh` produces a `#!/bin/sh exec dotnet "$DLL" "$@"` wrapper, not a
   standalone native binary. This is structurally different from C# NativeAOT.

3. **n-body uses AVX2 intrinsics (`Vector256<float>`) with an ARM64 fallback RID:**
   The `build_common.sh` includes a `linux-arm64` fallback RID. The `Vector256` + `Avx`
   intrinsic calls would throw `PlatformNotSupportedException` on ARM64. A latent
   portability bug; not an issue on the x86-64 measurement environment.

### Go

1. **regex-redux build is not a single-file `go build`:** flags.md states "each benchmark
   compiles a single `main.go` file." Regex-redux initializes a Go module, fetches
   `github.com/GRbit/go-pcre@v1.0.0`, builds the entire module directory, and requires
   CGO with a native C library (`pcre-dev`).

2. **`GOMAXPROCS` is set explicitly in several benchmarks, not via runtime defaults:**
   flags.md implies all benchmarks use runtime defaults. In reality:
   - `fannkuch-redux/main.go:149`: hardcodes `runtime.GOMAXPROCS(4)`
   - `fasta/main.go:159`: sets `GOMAXPROCS(runtime.NumCPU())`
   - `mandelbrot/main.go:114–115`: sets `GOMAXPROCS(runtime.NumCPU() * 2)`
   - `regex-redux/main.go:61`: sets `GOMAXPROCS(runtime.NumCPU())`
   - `spectral-norm/main.go:27–28`: sets `GOMAXPROCS(runtime.NumCPU() * 2)` via `init()`
   - Only binary-trees, k-nucleotide, and n-body use the unmodified Go runtime default.

### Haskell

1. **k-nucleotide: stale `-package ghc-compact` flag:** `k-nucleotide.yml` passes
   `-package ghc-compact` but `main.hs` does not import or use `GHC.Compact`. The flag
   is a no-op (the package exists so GHC does not error) but is misleading.

2. **fasta: `massiv` library not explicitly installed:** `fasta/main.hs` imports
   `Data.Massiv.Array` but `fasta.yml` has no `cabal install --lib massiv` step. The
   benchmark relies on `massiv` being present in the `haskell:9.10.1` Docker image.
   Not documented in flags.md; a potential portability risk.

3. **n-body: `-N4` reserves 4 RTS capabilities with no computational benefit:** The source
   is fully sequential. The `-threaded` flag adds GHC parallel RTS overhead (lock
   contention, GC synchronization across capabilities) with no benefit to computation.

### Java

1. **regex-redux `-Djava.library.path` documented with wrong literal path in flags.md:**
   flags.md states the path as `Include/java/jextract_pcre2`, but `build_in_tmp.sh`
   dynamically resolves it at build time using `find /usr/lib /lib -name 'libpcre2-8.so*'`.
   The actual path passed is the real PCRE2 library directory (e.g.,
   `/usr/lib/x86_64-linux-gnu`).

### Lua

1. **flags.md misclassifies the execution model as "no compilation step":** Every Lua
   benchmark runs `luac` in `build_in_tmp.sh` to pre-compile source to bytecode before
   the timed flow. The execution model remains interpretation at runtime, but there is a
   distinct build step that the flags.md description omits.

### OCaml

1. **fasta — `unix.cmxa` linked but unused in source:** `fasta/build_in_tmp.sh` links
   `unix.cmxa` but the source uses no `Unix.*` functions (only stdlib I/O). Over-linking
   with no correctness impact; consistent with docs and the CLBG reference pattern.

2. **spectral-norm — `unix.cmxa` linked but unused:** Same situation as fasta.

3. **regex-redux — uses pure-OCaml `re` library, not PCRE2:** Documented in flags.md as
   linking `re` or `re.pcre`. Both are OCaml pure-OCaml regex implementations with
   PCRE-syntax support, not a binding to the C PCRE2 library. This is a material
   algorithmic difference from C/C++/Rust benchmarks on this benchmark.

### Perl

1. **flags.md — Perl row is incomplete:** The Interpreted Languages table lists Perl as
   `perl` with no flags and no further detail. It omits: 6 of 8 benchmarks use Perl
   ithreads (`use threads`); regex-redux uses a fork+ithreads hybrid; fasta and n-body
   are single-threaded; and the `perl:5.42.1-threaded` image variant is architecturally
   required for `use threads` to function.

2. **fannkuch-redux thread count is input-bound, not CPU-bound:** Spawns 12 threads (=
   input N), which will oversubscribe the CPU on systems with fewer than 12 cores. This
   differs from all other multi-threaded Perl benchmarks, which read `/proc/cpuinfo`.

3. **regex-redux uses both `fork` and `threads` — the only benchmark with this hybrid
   model:** Parent does IUB substitutions while a forked child spawns 3 ithreads to
   count regex matches. Not documented anywhere in flags.md.

### PHP

1. **fannkuch-redux — flags.md omits extension flags:** `build_in_tmp.sh` loads
   `-dextension=shmop` and `-dextension=pcntl`, required because `main.php` uses
   `shmop_open`/`shmop_write`. Not documented in flags.md.

2. **k-nucleotide — `short_open_tag` not documented in flags.md:** `-d short_open_tag=1`
   is required because `main.php:1` uses the `<?` short open tag.

3. **mandelbrot — `short_open_tag` not documented in flags.md:** Same situation as
   k-nucleotide.

4. **n-body — `short_open_tag` undocumented; YML installs unused extensions:** `n-body.yml`
   installs `shmop pcntl sysvmsg` but none are used in `main.php` or loaded in the wrapper.

5. **spectral-norm — `short_open_tag` undocumented; YML installs shmop+sysvmsg
   unnecessarily:** Only `pcntl` is loaded in the spectral-norm wrapper; `shmop` and
   `sysvmsg` are installed via `docker-php-ext-install` but unused.

6. **fasta — YML installs shmop+pcntl but wrapper does not load them:** Source is
   single-threaded; both extensions are installed but have no effect.

### Python

1. **regex-redux: input file differs between production YAML and cluster-scenario YAML:**
   `benchmarks/python/regex-redux.yml` uses `fasta-25000000.txt`; the regex-redux flow in
   `gmt-cluster-scenario.yml` uses `fasta-25000000.txt` (half the input size). Inconsistent
   with all other benchmarks which use the same input in both contexts.

2. **flags.md does not document the `-OO` flag:** Applied to all 8 Python benchmarks. It
   strips `assert` statements and docstrings from bytecode. Not a minor detail — it
   removes asserts present in some source files and should be documented.

3. **spectral-norm: hardcoded pool size of 4 not adapted to CPU count:** Every other
   Python multiprocessing benchmark uses `cpu_count()`. Spectral-norm uses
   `Pool(processes=4)`. Not a YAML/source discrepancy but a notable behavioral outlier
   within the Python suite.

### Ruby

1. **flags.md does not document the `/opt/src/ruby-3.4.0/bin/ruby` probe:** All eight
   `build_in_tmp.sh` scripts check for a custom Ruby binary at this path before falling
   back to system `ruby`. The exact version used could differ if that path exists in
   the container.

2. **spectral-norm worker count (6) is hardcoded and undocumented:** All other multi-process
   Ruby benchmarks derive worker count from `/proc/cpuinfo`. Spectral-norm defaults to 6
   workers regardless of CPU count. Not mentioned in flags.md.

3. **k-nucleotide worker count (7) is fixed and undocumented:** flags.md records only
   runtime flags; the fixed-7-fork pattern is not described.

4. **regex-redux Thread+fork hybrid model is undocumented:** flags.md does not note that
   regex-redux uses 9 Threads each spawning a `Process.fork`, a two-layer concurrency
   model materially different from the MiniParallel CPU-scaled fork pools used by other
   benchmarks.

### Rust

1. **binary-trees and fannkuch-redux use `target-cpu=ivybridge`; all other 6 Rust
   benchmarks use `target-cpu=native`:** `ivybridge` caps the ISA to Ivy Bridge features
   (no AVX2, no BMI2, etc.). If the measurement host supports AVX2, auto-vectorization in
   binary-trees is restricted relative to the other six Rust benchmarks. This inconsistency
   is documented in `docs/flags.md:51–52` but may slightly penalize these two benchmarks.

2. **binary-trees and fannkuch-redux `build_in_tmp.sh` include a conditional
   `-L /opt/src/rust-libs` flag not documented in flags.md:** Takes effect only if that
   directory exists in the container; effectively a no-op in standard runs.

3. **binary-trees and fannkuch-redux binaries remain in the Cargo target directory** rather
   than being copied to `/tmp/rust-<bench>` as all other cargo-built Rust benchmarks do.
   No functional impact on measurement.

### Swift

1. **regex-redux uses NSRegularExpression (ICU) instead of PCRE2:** The other CLBG
   reference implementations (C, C++, Rust, Java) link against `libpcre2`. Swift's
   `NSRegularExpression` uses the ICU regex engine (part of Foundation on Linux). This is
   a material implementation difference that affects both runtime and energy measurements,
   making Swift regex-redux algorithmically non-comparable to the PCRE2-using
   implementations on an equal footing.

2. **Binary name inconsistency across Swift benchmarks:** n-body, regex-redux, and
   spectral-norm use CLBG-derived names with numeric suffixes (e.g., `nbody.swift-3.swift_run`);
   the other five benchmarks use `swift-<benchmark>`. No effect on correctness or
   performance but is an inconsistency in the build output naming convention.

---

## 5. Per-Language File Index

- [C](c_benchmark_insights.md)
- [C++](cpp_benchmark_insights.md)
- [C#](csharp_benchmark_insights.md)
- [Dart](dart_benchmark_insights.md)
- [Erlang](erlang_benchmark_insights.md)
- [F#](fsharp_benchmark_insights.md)
- [Go](go_benchmark_insights.md)
- [Haskell](haskell_benchmark_insights.md)
- [Java](java_benchmark_insights.md)
- [Lua](lua_benchmark_insights.md)
- [NodeJS](nodejs_benchmark_insights.md)
- [OCaml](ocaml_benchmark_insights.md)
- [Perl](perl_benchmark_insights.md)
- [PHP](php_benchmark_insights.md)
- [Python](python_benchmark_insights.md)
- [Ruby](ruby_benchmark_insights.md)
- [Rust](rust_benchmark_insights.md)
- [Swift](swift_benchmark_insights.md)
