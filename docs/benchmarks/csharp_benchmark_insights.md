# C# Benchmark Insights

**Language:** C# (.NET 9.0)
**Runtime model:** NativeAOT — compiled to a standalone native binary via `dotnet publish -c Release` with `PublishAot=true`. There is NO CLR/JIT and NO JIT warmup; the binary executes as pure ahead-of-time compiled native code identical in character to a C or Rust binary.
**Docker image:** `mcr.microsoft.com/dotnet/sdk:9.0` (confirmed in every `<benchmark>.yml`, e.g. `binary-trees.yml:6`)
**Build entry point:** `benchmarks/csharp/build_common.sh` — all 8 benchmarks delegate to this single shared script via a one-line per-benchmark `build_in_tmp.sh` (e.g. `binary-trees/build_in_tmp.sh:4`).

---

## Per-Benchmark Breakdown

> **Binary-Trees — C#**
> - Execution: AOT via NativeAOT (.NET 9.0); image `mcr.microsoft.com/dotnet/sdk:9.0`; binary at `/tmp/csharp-binary-trees`; run with argument `21` (test profile: `6`). (`binary-trees.yml:18`, `binary-trees_test.yml:18`)
> - Concurrency: **Multi-threaded** via `Task.Run`. Exactly `NoTasks = 4` tasks are spawned per depth level (`main.cs:13`, `main.cs:34`). Each task independently builds and sums trees. Thread count is hardcoded to 4, does not scale with CPU count.
> - Build/runtime config: `PublishAot=true`, `OptimizationPreference=Speed`, `IlcInstructionSet=native`, `TargetFramework=net9.0`, `AllowUnsafeBlocks=true`, `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`. No per-benchmark csproj overrides. (`build_common.sh:59–61`)
> - Source of flags: `benchmarks/csharp/build_common.sh:48–78`
> - Notes: Server GC is particularly relevant here — the benchmark performs heavy GC-pressure allocation (many short-lived tree nodes). Server GC with concurrent collection significantly improves throughput under multi-threaded allocation. No SIMD or unsafe code in the source.

---

> **Fannkuch-Redux — C#**
> - Execution: AOT via NativeAOT (.NET 9.0); binary at `/tmp/csharp-fannkuch-redux`; run with argument `12` (test profile not checked, but build is identical). (`fannkuch-redux.yml:18`)
> - Concurrency: **Multi-threaded** via `new Thread(...)`. Exactly `nThreads = 4` OS threads are created (`main.cs:47–53`). Work is partitioned into `maxBlocks * nThreads` blocks (`main.cs:48–49`); threads atomically claim blocks via `Interlocked.Decrement(ref _blockCount)` (`main.cs:86`). Thread count hardcoded to 4, does not scale with CPU count.
> - Build/runtime config: Identical shared settings as all other benchmarks. (`build_common.sh:48–78`)
> - Source of flags: `benchmarks/csharp/build_common.sh:48–78`
> - Notes: Heavy SIMD use — entire inner loop operates on `Vector128<byte>` via SSE2/SSE3/SSE4.1/SSSE3 intrinsics (`main.cs:17–18`, `main.cs:63–75`). `[MethodImpl(MethodImplOptions.AggressiveOptimization)]` on both `Main` and `pfannkuchThread` (`main.cs:30`, `main.cs:61`). `IlcInstructionSet=native` ensures the AOT compiler emits host-native SIMD. This is among the most compute-intensive and SIMD-heavy benchmarks in the C# suite.

---

> **Fasta — C#**
> - Execution: AOT via NativeAOT (.NET 9.0); binary at `/tmp/csharp-fasta`; run with argument `25000000`. (`fasta.yml:18`)
> - Concurrency: **Multi-threaded** via `ThreadPool.QueueUserWorkItem`. The `WriteRandom` function queues one work item per block into the ThreadPool (`main.cs:87–98`). An outer `ThreadPool.QueueUserWorkItem` wraps the two `WriteRandom` calls for the IUB and frequency sections (`main.cs:110–126`). The main thread writes the ALU repeat section and then reads results serially in order, spin-waiting (`Thread.Sleep(0)`) if a block is not yet ready (`main.cs:156`). Thread count is determined by the ThreadPool (unbounded, scales with available processors at runtime).
> - Build/runtime config: Identical shared settings. (`build_common.sh:48–78`)
> - Source of flags: `benchmarks/csharp/build_common.sh:48–78`
> - Notes: Uses `ArrayPool<byte>` and `ArrayPool<int>` for buffer reuse (`main.cs:27–28`). `[MethodImpl(MethodImplOptions.AggressiveInlining)]` on hot helpers (`main.cs:30`, `main.cs:45`, `main.cs:66`). Thread count is NOT hardcoded — the ThreadPool size scales with available cores, making this the only C# benchmark where actual parallelism degree is CPU-count-dependent at runtime.

---

> **K-Nucleotide — C#**
> - Execution: AOT via NativeAOT (.NET 9.0); binary at `/tmp/csharp-k-nucleotide`; takes FASTA input via stdin (`< /tmp/repo/inputs/fasta-2500000.txt`). (`k-nucleotide.yml:19`)
> - Concurrency: **Multi-threaded** via `Task.Run` and `Parallel.ForEach`. Input blocks are decoded in parallel via `Parallel.ForEach(threeBlocks, ...)` (`main.cs:190`). Seven counting tasks are launched concurrently with `Task.Run` (`main.cs:196–202`), each scanning the full dataset for a different k-mer length. Tasks run on the default ThreadPool, scaling with CPU count.
> - Build/runtime config: Identical shared settings **plus** a NuGet package reference: `Microsoft.Experimental.Collections` version `1.0.6-e190117-3` (for `DictionarySlim<TKey,TValue>`). This is the only benchmark with a per-benchmark csproj addition. (`build_common.sh:68–74`)
> - Source of flags: `benchmarks/csharp/build_common.sh:48–78`
> - Notes: `DictionarySlim` from `Microsoft.Collections.Extensions` is used for hash-map counting (`main.cs:16`, `main.cs:116`). Parallelism degree for both `Parallel.ForEach` and `Task.Run` is ThreadPool-managed and scales with CPU count. Server GC + concurrent GC reduces GC pauses during heavy hash-table allocation.

---

> **Mandelbrot — C#**
> - Execution: AOT via NativeAOT (.NET 9.0); binary at `/tmp/csharp-mandelbrot`; run with argument `16000` (16000×16000 pixel PBM). (`mandelbrot.yml:18`)
> - Concurrency: **Multi-threaded** via `Parallel.For`. Two `Parallel.For` loops: first precomputes `Cr0Array` over `lineSize` entries (`main.cs:36–38`), then computes pixel rows over `lineCount` (`main.cs:40–49`). Both loops run on the default ThreadPool; degree of parallelism scales with available CPU cores.
> - Build/runtime config: Identical shared settings. (`build_common.sh:48–78`)
> - Source of flags: `benchmarks/csharp/build_common.sh:48–78`
> - Notes: Intensive SIMD use — inner Mandelbrot kernel operates on `Vector512<double>` (AVX-512 width, 8 doubles per vector) (`main.cs:30`, `main.cs:55–91`). Early-exit optimization: for pixels previously determined inside the set, uses the full 50-iteration path; for new pixels, batches 5 iterations at a time and breaks on divergence (`main.cs:65–76`). `[MethodImpl(MethodImplOptions.AggressiveInlining)]` on the kernel (`main.cs:54`). `IlcInstructionSet=native` is critical to unlock AVX-512 at AOT compile time.

---

> **N-Body — C#**
> - Execution: AOT via NativeAOT (.NET 9.0); binary at `/tmp/csharp-n-body`; run with argument `50000000`. (`n-body.yml:18`)
> - Concurrency: **Single-threaded**. All computation in `Advance` and `Energy` runs on the main thread with no threads, tasks, or parallel constructs of any kind. (`main.cs:53–114`)
> - Build/runtime config: Identical shared settings. (`build_common.sh:48–78`)
> - Source of flags: `benchmarks/csharp/build_common.sh:48–78`
> - Notes: Heavy AVX2 SIMD via `System.Runtime.Intrinsics.X86.Avx` — all body positions, velocities, and masses are `Vector256<double>` (`main.cs:17–18`). Uses `unsafe` with raw pointers and stack allocation (`stackalloc V256d[18]`) with manual 32-byte alignment (`main.cs:162–163`). `[MethodImpl(AggressiveOptimization | AggressiveInlining)]` and `[SkipLocalsInit]` on all hot methods (`main.cs:21`, `main.cs:29`, `main.cs:41`). A `goto ADVANCE` tight loop drives the simulation (`main.cs:64–70`). This is the most unsafe/pointer-heavy benchmark in the C# suite. `AllowUnsafeBlocks=true` is mandatory.

---

> **Regex-Redux — C#**
> - Execution: AOT via NativeAOT (.NET 9.0); binary at `/tmp/csharp-regex-redux`; takes FASTA input via stdin (`< /tmp/repo/inputs/fasta-5000000.txt`). (`regex-redux.yml:21`)
> - Concurrency: **Multi-threaded** via `Task.Run` and PLINQ (`AsParallel`). The substitution chain runs in a background `Task.Run` (`main.cs:27–38`). The 9 match-counting regex queries run via `regexes.AsParallel().AsOrdered()` (`main.cs:53`). Both paths run on the ThreadPool, scaling with CPU count.
> - Build/runtime config: Identical shared settings. Additionally requires `libpcre2-8` installed at build time (`regex-redux.yml:11`). The C# `Pcre` class wraps the native `pcre2-8` library via P/Invoke (`DllImport("pcre2-8", ...)`) with JIT compilation of patterns (`main.cs:100`, `main.cs:142–164`). `AllowUnsafeBlocks=true` is required for the `unsafe` pointer operations in `Replace` and `Exec` (`main.cs:122–130`, `main.cs:134–138`).
> - Source of flags: `benchmarks/csharp/build_common.sh:48–78`; extra dep: `regex-redux.yml:11`
> - Notes: Unlike most CLBG regex-redux implementations that use the managed .NET `Regex`, this uses native PCRE2 via P/Invoke with JIT-compiled patterns. PCRE2's own JIT (`pcre2_jit_compile_8`) is distinct from and independent of the .NET NativeAOT compilation — pattern matching is handled entirely by the native PCRE2 engine's own JIT at runtime. The NativeAOT binary itself still has no CLR JIT warmup.

---

> **Spectral-Norm — C#**
> - Execution: AOT via NativeAOT (.NET 9.0); binary at `/tmp/csharp-spectral-norm`; run with argument `5500`. (`spectral-norm.yml:18`)
> - Concurrency: **Multi-threaded** via `Parallel.For`. Both `mult_Av` and `mult_Atv` use `Parallel.For(0, n, ...)` over the `n` rows of the matrix-vector products (`main.cs:54`, `main.cs:72`). These are called 20 times total in the power-iteration loop (`main.cs:27`). Thread count is ThreadPool-managed and scales with CPU count.
> - Build/runtime config: Identical shared settings. (`build_common.sh:48–78`)
> - Source of flags: `benchmarks/csharp/build_common.sh:48–78`
> - Notes: Uses SSE2/SSE3 intrinsics — inner loop loads 2 doubles per iteration via `Sse2.LoadVector128` and accumulates with `Sse3.HorizontalAdd` (`main.cs:59–64`, `main.cs:75–80`). `[MethodImpl(MethodImplOptions.AggressiveOptimization)]` on both `mult_Av` and `mult_Atv` (`main.cs:51`, `main.cs:70`). Uses `unsafe` with raw pointers throughout (`main.cs:16`).

---

## Discrepancy log

One discrepancy noted:

- **`flags.md` states** (line 138): "All benchmarks use identical project settings — no per-benchmark overrides."
  **Actual behavior:** `build_common.sh:68–74` adds a `<ItemGroup><PackageReference ...></ItemGroup>` block for `Microsoft.Experimental.Collections` specifically when `BENCH = "k-nucleotide"`. This is a per-benchmark csproj override not reflected in the flags.md summary. The flags.md should note that k-nucleotide adds the `Microsoft.Experimental.Collections` NuGet package (same discrepancy exists in the F# section of flags.md, which does correctly document it for F# at line 159).

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|---|---|---|---|---|
| C# | NativeAOT (`dotnet publish`, `PublishAot=true`) | `OptimizationPreference=Speed`, `IlcInstructionSet=native`, `AllowUnsafeBlocks=true`, `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`, `net9.0` | Mixed: single-threaded (n-body); fixed-4-thread (binary-trees via `Task.Run`, fannkuch-redux via `new Thread`); ThreadPool/CPU-scaled (fasta via `ThreadPool.QueueUserWorkItem`, k-nucleotide via `Task.Run`+`Parallel.ForEach`, mandelbrot via `Parallel.For`, regex-redux via `Task.Run`+PLINQ, spectral-norm via `Parallel.For`) | No JIT warmup; SIMD used in 5/8 benchmarks (fannkuch-redux: SSE2/SSE4.1/SSSE3 `Vector128`; mandelbrot: AVX-512 `Vector512`; n-body: AVX2 `Vector256`; spectral-norm: SSE2/SSE3 `Vector128`; fasta: implicit via inlining). regex-redux uses native PCRE2 via P/Invoke with PCRE2's own JIT. k-nucleotide adds `Microsoft.Experimental.Collections` NuGet dep. Server+Concurrent GC benefits all multi-threaded benchmarks. |
