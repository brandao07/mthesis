# C++ Benchmark Insights

**Language:** C++  
**Compiler:** `g++` (GCC 15.2.0)  
**Docker image:** `gcc:15.2.0` (all benchmarks)

No `build_in_tmp.sh` is used for any C++ benchmark — all compile flags are inlined directly into `setup-commands` within each YAML file.

---

> **Binary-Trees — C++**
> - Execution: AOT native binary via `g++ (GCC 15.2.0)` with `-pipe -O3 -fomit-frame-pointer -march=native -std=gnu++17 -ltbb`
> - Concurrency: **Multi-threaded**; uses C++17 parallel STL (`std::execution::par`) backed by Intel TBB (`-ltbb`). Two nested parallel calls: `std::for_each(std::execution::par, ...)` over depth levels, and `std::transform_reduce(std::execution::par, ...)` over tree iterations within each depth. Thread pool managed by TBB — scales with available CPUs automatically. Each thread uses a `thread_local std::pmr::unsynchronized_pool_resource` for lock-free memory allocation.
> - Build/runtime config: `-O3 -fomit-frame-pointer -march=native -std=gnu++17 -ltbb`. Note: `-std=gnu++17` (GNU dialect) rather than `-std=c++17`. Uses `std::pmr::monotonic_buffer_resource` for arena allocation. Runtime arg: `21` (tree depth).
> - Source of flags: `benchmarks/cpp/binary-trees.yml:11`; concurrency confirmed at `benchmarks/cpp/binary-trees/main.cpp:74,79`; thread-local allocator at `main.cpp:84`

---

> **Fannkuch-Redux — C++**
> - Execution: AOT native binary via `g++ (GCC 15.2.0)` with `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -fopenmp`
> - Concurrency: **Multi-threaded**; uses OpenMP `#pragma omp parallel for` with `reduction(max:max_flips)` and `reduction(+:checksum)` (`main.cpp:149-151`). Thread count is determined by OpenMP at runtime (default: all available cores). Also uses SSE2/SSSE3 SIMD intrinsics (`__m128i`, `_mm_shuffle_epi8`, `_mm_extract_epi8`) from `<immintrin.h>` for permutation operations (`main.cpp:15,125,135`). Parallelism is over permutation blocks (`max_blocks = 24`, `main.cpp:80`).
> - Build/runtime config: `-O3 -fomit-frame-pointer -march=native -std=c++17 -fopenmp`. Runtime arg: `12` (n=12).
> - Source of flags: `benchmarks/cpp/fannkuch-redux.yml:9`; OpenMP pragma at `benchmarks/cpp/fannkuch-redux/main.cpp:149`; SIMD includes at `main.cpp:15`

---

> **Fasta — C++**
> - Execution: AOT native binary via `g++ (GCC 15.2.0)` with `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -lpthread`
> - Concurrency: **Multi-threaded**; uses `std::thread` directly (`<thread>`, `main.cpp:18`). Thread count: `NUM_THREADS = 2` capped by `std::thread::hardware_concurrency()` (`main.cpp:33,261`). Two threads share work via a `RandomLCG` generator and a `Writer` object, both protected by a custom spinlock (`SpinLock` using `std::atomic_bool`, `main.cpp:36-51`). Also uses SSE2 SIMD intrinsics (`#ifdef __SSE2__`, `_mm_pause()`, `_mm_set1_epi32`, `_mm_cmplt_epi32`) for the nucleotide lookup (`main.cpp:21-24,60-66,88-99`). Uses `boost::range::adaptor::strided` and `boost::irange` (`main.cpp:25-26`).
> - Build/runtime config: `-O3 -fomit-frame-pointer -march=native -std=c++17 -lpthread`. Requires `libboost-dev` (installed in `setup-commands`). Runtime arg: `25000000`.
> - Source of flags: `benchmarks/cpp/fasta.yml:11`; thread count at `benchmarks/cpp/fasta/main.cpp:33,261`; SSE2 at `main.cpp:21-23`

---

> **K-Nucleotide — C++**
> - Execution: AOT native binary via `g++ (GCC 15.2.0)` with `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -lpthread`
> - Concurrency: **Multi-threaded**; uses `std::thread` directly (`<thread>`, `main.cpp:37`). Thread count: compile-time constant `Cfg::thread_count = 4` (`main.cpp:45`). In `CalculateInThreads<size>()`, 4 threads are created and joined; each thread computes hash frequencies on a separate `__gnu_pbds::cc_hash_table` partition, then partial tables are merged on the main thread after join (`main.cpp:152-171`). No SIMD intrinsics in source; compiler may auto-vectorize via `-march=native`.
> - Build/runtime config: `-O3 -fomit-frame-pointer -march=native -std=c++17 -lpthread`. Uses GCC's policy-based data structure (`__gnu_pbds::cc_hash_table`, `main.cpp:42,121`). Input: `fasta-2500000.txt` via stdin redirect.
> - Source of flags: `benchmarks/cpp/k-nucleotide.yml:9`; thread count at `benchmarks/cpp/k-nucleotide/main.cpp:45`; thread launch at `main.cpp:159-162`

---

> **Mandelbrot — C++**
> - Execution: AOT native binary via `g++ (GCC 15.2.0)` with `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -mno-fma -pthread`
> - Concurrency: **Multi-threaded**; uses `std::thread` directly (`<thread>`, `main.cpp:14`). Thread count: `std::thread::hardware_concurrency()` stored in `numberOfCpuCores` (`main.cpp:24`); one thread per interlaced canvas strip, so thread count scales with all available CPU cores. Uses conditional SIMD: `Simd512DUnion` (`__m512d`, AVX-512) if `__AVX512BW__` defined; else `Simd256DUnion` (`__m256d`, AVX) if `__AVX__`; else `Simd128DUnion` (`__m128d`, SSE) if `__SSE__`; else scalar fallback (`main.cpp:434-443`). `-march=native` enables the widest available ISA at build time. `-mno-fma` disables fused multiply-add to match the reference output precisely.
> - Build/runtime config: `-O3 -fomit-frame-pointer -march=native -std=c++17 -mno-fma -pthread`. Runtime arg: `16000` (bitmap size 16000×16000). Note: flag is `-pthread` (linker+compiler flag combo), not `-lpthread` (linker only) — semantically equivalent on GCC but the YAML uses `-pthread`.
> - Source of flags: `benchmarks/cpp/mandelbrot.yml:9`; thread count at `benchmarks/cpp/mandelbrot/main.cpp:24,457`; SIMD dispatch at `main.cpp:434-443`

---

> **N-Body — C++**
> - Execution: AOT native binary via `g++ (GCC 15.2.0)` with `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17`
> - Concurrency: **Single-threaded**; no threading primitives in source. All computation is sequential. Heavy use of AVX2 SIMD intrinsics (`__m256d`, `_mm256_*`) hard-coded throughout `NBodySystem` (`main.cpp:19`). Uses a custom `_mm256_rsqrt_pd` implementing Goldschmidt's algorithm in AVX2 (`main.cpp:23-36`). Compile-time loop unrolling via recursive templates (`KernelLoop0`, `KernelLoop1`, `AdvanceLoopInner0/1/2`, `main.cpp:124-226`). AVX2 is required unconditionally — the code will not compile or run correctly without it; `-march=native` enables it on a capable host.
> - Build/runtime config: `-O3 -fomit-frame-pointer -march=native -std=c++17`. No threading library linked. Runtime arg: `50000000` (simulation steps).
> - Source of flags: `benchmarks/cpp/n-body.yml:9`; AVX2 intrinsics at `benchmarks/cpp/n-body/main.cpp:18-19`; no thread includes

---

> **Regex-Redux — C++**
> - Execution: AOT native binary via `g++ (GCC 15.2.0)` with `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -lpcre2-8 -lpthread`
> - Concurrency: **Multi-threaded**; uses `std::async(std::launch::async, ...)` backed by `<future>` (`main.cpp:18,296`). In `count_occurrences()`, 9 regex-counting tasks are launched as `std::async(launch_type, ...)` — one per pattern — running concurrently in separate threads (`main.cpp:326-334`). A 10th async task is launched in `main()` to run all 9 counting tasks concurrently with the sequential replacement pipeline (`main.cpp:375-376`). Maximum concurrency: up to 10 simultaneous threads. Uses PCRE2's JIT compilation (`pcre2_jit_compile`, `pcre2_jit_match`) for runtime regex compilation to machine code (`main.cpp:229,199`). Uses `boost::noncopyable` (`main.cpp:15`).
> - Build/runtime config: `-O3 -fomit-frame-pointer -march=native -std=c++17 -lpcre2-8 -lpthread`. Requires `libboost-dev` (for `boost/noncopyable.hpp`). Input: `fasta-5000000.txt` via stdin redirect. Note: libpcre2 is already present in the base `gcc:15.2.0` image; only `libboost-dev` is installed in `setup-commands`.
> - Source of flags: `benchmarks/cpp/regex-redux.yml:11`; async launch at `benchmarks/cpp/regex-redux/main.cpp:296,330`; PCRE2 JIT at `main.cpp:229`

---

> **Spectral-Norm — C++**
> - Execution: AOT native binary via `g++ (GCC 15.2.0)` with `-pipe -O3 -fomit-frame-pointer -march=native -fopenmp`
> - Concurrency: **Multi-threaded**; uses OpenMP `#pragma omp parallel` with `num_threads(GetThreadCount())` where `GetThreadCount()` reads CPU affinity via `sched_getaffinity()` to count available cores (`main.cpp:74-85,94`). Thread count scales with all CPU cores in the affinity set. Uses SSE2 intrinsics (`__m128d`, `_mm_set_pd`, `_mm_storeu_pd`) from `<emmintrin.h>` for vectorized matrix-vector products (`main.cpp:18,31-47`). Note: `-std=c++17` is absent from the compile command — this benchmark is compiled without an explicit C++ standard flag.
> - Build/runtime config: `-O3 -fomit-frame-pointer -march=native -fopenmp` (no `-std` flag). Runtime arg: `5500` (matrix size N=5500).
> - Source of flags: `benchmarks/cpp/spectral-norm.yml:9`; thread count via affinity at `benchmarks/cpp/spectral-norm/main.cpp:74-85`; SSE2 at `main.cpp:18`

---

## Discrepancy log

1. **Binary-trees — `libboost-dev` install claim in `docs/flags.md`**: `flags.md` (line 28) states "All benchmarks install `libboost-dev` in `setup-commands`." This is **false** for several benchmarks. Verified per-benchmark:
   - `binary-trees.yml`: installs `libtbb-dev libboost-dev` — correct.
   - `fasta.yml`: installs `libboost-dev` only — correct.
   - `regex-redux.yml`: installs `libboost-dev` only — correct (boost header `boost/noncopyable.hpp` is used).
   - `fannkuch-redux.yml`: **no apt-get install step at all** — no boost or tbb installed. The source (`main.cpp`) does not include any Boost headers, so this is correct behavior but contradicts the "all benchmarks install `libboost-dev`" claim.
   - `k-nucleotide.yml`: **no apt-get install step**. The source uses `__gnu_pbds` (GCC built-in), not Boost. No Boost install is needed or performed — contradicts the "all benchmarks install `libboost-dev`" claim.
   - `mandelbrot.yml`: **no apt-get install step**. No Boost headers in source — contradicts the claim.
   - `n-body.yml`: **no apt-get install step**. No Boost headers in source — contradicts the claim.
   - `spectral-norm.yml`: **no apt-get install step**. No Boost headers in source — contradicts the claim.

2. **Spectral-norm — missing `-std` flag in `flags.md`**: `flags.md` (line 39) documents spectral-norm flags as `-pipe -O3 -fomit-frame-pointer -march=native -fopenmp` with no `-std` flag. The actual `spectral-norm.yml` (line 9) confirms this — no `-std=c++17` is passed. This is a real difference from all other benchmarks and matches the YAML. The source file header comment also omits a `-std` flag. This is consistent and documented, but notable: spectral-norm is the only C++ benchmark compiled without an explicit C++ standard.

3. **Mandelbrot — `-pthread` vs `-lpthread`**: `flags.md` (line 37) documents `-pthread`. The YAML (`mandelbrot.yml:9`) uses `-pthread` (not `-lpthread`). The fasta and k-nucleotide YAMLs use `-lpthread`. These are semantically equivalent on GCC but are not the same flag. The `flags.md` entry is accurate for mandelbrot specifically.

4. **Binary-trees — `-std=gnu++17` vs `-std=c++17`**: `flags.md` (line 32) correctly notes `-std=gnu++17` for binary-trees. All other benchmarks with an explicit standard use `-std=c++17`. This is the only benchmark using the GNU dialect extension.

5. **Fasta — thread count capped at 2**: `flags.md` (line 34) notes `-lpthread` for fasta but does not mention the hard-coded `NUM_THREADS = 2` cap. The source at `main.cpp:33` defines `constexpr int NUM_THREADS = 2`, making fasta the only benchmark with a fixed low thread count regardless of CPU count.

6. **Regex-redux — `libpcre2-8` presence in image**: `flags.md` implies `libpcre2-8` needs to be installed, but the `regex-redux.yml` `setup-commands` only installs `libboost-dev`, not `libpcre2-dev`. The `gcc:15.2.0` base image appears to include PCRE2 libraries, or the dynamic linker resolves it. The bundled `pcre2.h` header (`benchmarks/cpp/regex-redux/pcre2.h`) is used at compile time, making a system `libpcre2-dev` unnecessary for compilation; only the shared library (`-lpcre2-8`) is needed at link/runtime.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| C++ | AOT (g++ → native binary, GCC 15.2.0) | `-O3 -fomit-frame-pointer -march=native` (all); `-std=gnu++17 -ltbb` (binary-trees); `-std=c++17 -fopenmp` (fannkuch-redux, spectral-norm); `-std=c++17 -lpthread` (fasta, k-nucleotide); `-std=c++17 -mno-fma -pthread` (mandelbrot); `-std=c++17` (n-body); `-std=c++17 -lpcre2-8 -lpthread` (regex-redux); no `-std` (spectral-norm) | Per-benchmark: binary-trees=TBB parallel STL (all CPUs); fannkuch-redux=OpenMP (all CPUs) + SSE2/SSSE3 SIMD; fasta=std::thread fixed 2 threads + SSE2 SIMD; k-nucleotide=std::thread fixed 4 threads; mandelbrot=std::thread all CPUs + AVX-512/AVX/SSE adaptive SIMD; n-body=single-threaded + hard-coded AVX2 SIMD; regex-redux=std::async up to 10 threads + PCRE2 JIT; spectral-norm=OpenMP all CPUs + SSE2 SIMD | Only benchmark compiled single-threaded: n-body. Only benchmark without `-std` flag: spectral-norm. Only benchmark using GNU dialect (`-std=gnu++17`): binary-trees. Fasta hard-caps threads at 2 regardless of CPU count. N-body unconditionally requires AVX2. Regex-redux uses PCRE2's own JIT (runtime codegen inside a statically-compiled binary). `docs/flags.md` incorrectly states all benchmarks install `libboost-dev` — only binary-trees, fasta, and regex-redux do. |
