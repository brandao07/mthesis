# F# Benchmark Insights

**Language:** F#
**.NET version:** net9.0
**Docker image:** `mcr.microsoft.com/dotnet/sdk:9.0` (all benchmarks)
**Compilation type:** JIT via CLR — `dotnet build` (NOT AOT; `PublishAot=false`)
**Warmup note:** Because the output is a shell wrapper (`exec dotnet "<dll>" "$@"`) rather than a native binary, every run starts the CLR from scratch: JIT compilation of hot methods occurs at process start. This adds a measurable warmup cost absent in NativeAOT languages (C# in this repo, Rust, etc.) and makes cold-start energy cost structurally higher for F# than for AOT peers.

Source of shared build config: `benchmarks/fsharp/build_common.sh:48–76`

---

## Per-Benchmark Breakdown

---

> **binary-trees — F#**
> - **Execution:** JIT via CLR (.NET 9.0, `dotnet build`). Output: `/tmp/fsharp-binary-trees` shell wrapper → `exec dotnet "<dll>"`. Build config: `PublishAot=false`, `ImplicitUsings=enable`, `Nullable=enable`, `AllowUnsafeBlocks=true`. Canonical run: `n=21`. Test run: `n=6`.
> - **Concurrency:** Multi-threaded. Uses F# `Async.Parallel` to run one async computation per depth level (`for depth in minDepth..2..maxDepth`). At `n=21` (minDepth=4, maxDepth=21) that is 9 parallel async tasks dispatched to the CLR thread pool. Thread count scales with the number of depth levels, bounded by CLR thread pool size (not explicitly capped). Does NOT scale with `Environment.ProcessorCount`.
> - **Build/runtime config:** `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true` (server GC enables one heap per logical CPU, important for parallel allocation in this tree-heavy benchmark). No SIMD. `setup_dependencies.sh` called at setup (pre-warms NuGet cache).
> - **Source of flags:** `build_common.sh:48–76` (`.fsproj` generation); concurrency: `binary-trees/main.fs:30–38` (`Async.Parallel` + `Async.RunSynchronously`); YML: `binary-trees.yml:18`.

---

> **fannkuch-redux — F#**
> - **Execution:** JIT via CLR (.NET 9.0, `dotnet build`). Output: `/tmp/fsharp-fannkuch-redux` shell wrapper. Canonical run: `n=12`. Test run: `n=7` (inferred from default in source).
> - **Concurrency:** Multi-threaded. Partitions factorial permutations into `Environment.ProcessorCount` equal-sized tasks, each run as an `async` computation via `Async.Parallel` + `Async.RunSynchronously` (`main.fs:103–109`). Thread count equals `System.Environment.ProcessorCount` at runtime — scales with available logical CPUs. Uses `NativePtr.stackalloc` (unsafe native pointer arithmetic) for inner-loop permutation state.
> - **Build/runtime config:** `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`. `#nowarn "9"` suppresses unsafe-pointer warnings; `AllowUnsafeBlocks=true` is required. `setup_dependencies.sh` called at setup.
> - **Source of flags:** `build_common.sh:48–76`; concurrency: `fannkuch-redux/main.fs:103–109`; YML: `fannkuch-redux.yml:18`.

---

> **fasta — F#**
> - **Execution:** JIT via CLR (.NET 9.0, `dotnet build`). Output: `/tmp/fsharp-fasta` shell wrapper. Canonical run: `n=25000000`. Test run: not inspected but follows standard pattern.
> - **Concurrency:** Multi-threaded via `System.Threading.Tasks.Task`. Uses `Task.Run` to asynchronously generate random-sequence blocks in the background while the main thread writes the ALU repeat sequence synchronously to stdout. Per-block byte generation is dispatched as individual `Task.Run` closures stored in a `tasks` array (`fasta/main.fs:57–63`). Thread count is pool-managed; up to `noTasks` parallel tasks may be in flight.
> - **Build/runtime config:** `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`. No SIMD. Uses `System.Buffers.ArrayPool.Shared` for buffer recycling. Notably, `fasta.yml` does **not** call `setup_dependencies.sh` in its setup-commands (only `build_in_tmp.sh`) — the only benchmark besides mandelbrot with this pattern.
> - **Source of flags:** `build_common.sh:48–76`; concurrency: `fasta/main.fs:26–63` (`Task.Run` dispatching); YML: `fasta.yml:9`.

---

> **k-nucleotide — F#**
> - **Execution:** JIT via CLR (.NET 9.0, `dotnet build`). Output: `/tmp/fsharp-k-nucleotide` shell wrapper. Canonical run: reads from `fasta-25000000.txt` via stdin. Extra NuGet dependency: `Microsoft.Experimental.Collections` 1.0.6-e190117-3 (`DictionarySlim`).
> - **Concurrency:** Multi-threaded via F# `Async.Parallel`. Seven async computations are composed via `Async.Parallel` at `main.fs:200–209`, each independently counting or computing frequency tables for different k-mer lengths (1, 2, 3, 4, 6, 12, 18). Additionally, inside `count64`, four sub-tasks per computation run in parallel (`Seq.init 4 (fun i -> async { ... }) |> Async.Parallel`, `main.fs:181–184`). Also uses `Array.Parallel.iter` to map DNA byte encoding across input blocks (`main.fs:98–101`). Thread count: pool-managed, effectively up to `4 × outer_tasks` concurrent async operations.
> - **Build/runtime config:** `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`. Extra `<PackageReference Include="Microsoft.Experimental.Collections" Version="1.0.6-e190117-3" />` in generated `.fsproj` (`build_common.sh:63–69`). `setup_dependencies.sh` pre-restores this NuGet package into `/tmp/nuget-packages` before build.
> - **Source of flags:** `build_common.sh:48–76`, NuGet section `build_common.sh:63–69`; concurrency: `k-nucleotide/main.fs:98–101, 181–184, 200–209`; YML: `k-nucleotide.yml:18–19`.

---

> **mandelbrot — F#**
> - **Execution:** JIT via CLR (.NET 9.0, `dotnet build`). Output: `/tmp/fsharp-mandelbrot` shell wrapper. Canonical run: `n=16000`. Test run: `n=200` (source default).
> - **Concurrency:** Multi-threaded via `System.Threading.Tasks.Parallel.For`. `Parallel.For(0, size, fun y -> ...)` at `mandelbrot/main.fs:67–72` parallelises row computation across CLR thread pool threads. Thread count: pool-managed, scales with logical CPU count (standard `Parallel.For` partitioner).
> - **Build/runtime config:** `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`. SIMD: uses `System.Numerics.Vector<float>` (platform-width SIMD; `#nowarn "9"` + `NativePtr` for unsafe memory access). Also uses `System.Runtime.CompilerServices.Unsafe.Read/Write` for direct pointer dereference. `mandelbrot.yml` does **not** call `setup_dependencies.sh` (only `build_in_tmp.sh`).
> - **Source of flags:** `build_common.sh:48–76`; concurrency: `mandelbrot/main.fs:67–72` (`Parallel.For`); SIMD: `mandelbrot/main.fs:1–16` (`open System.Numerics`); YML: `mandelbrot.yml:9`.

---

> **n-body — F#**
> - **Execution:** JIT via CLR (.NET 9.0, `dotnet build`). Output: `/tmp/fsharp-n-body` shell wrapper. Canonical run: `n=50000000`. Test run: uses default from args parsing.
> - **Concurrency:** Single-threaded. All computation (`advance`, `energy`) runs sequentially in the main thread. No `Async`, `Task`, `Parallel.For`, or threading primitives present in source.
> - **Build/runtime config:** `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`. SIMD: uses `System.Runtime.Intrinsics.Vector256<float>` with explicit AVX intrinsics (`Avx.Multiply`, `Avx.Add`, `Avx.Subtract`, `Avx.Divide`) via `open System.Runtime.Intrinsics.X86` (`n-body/main.fs:8–9, 16–20`). Stack-allocated `Span<Vector256<float>>` for planet state (`n-body/main.fs:127–130`). This is x86-specific AVX2 code; the build script targets `linux-x64` by default, with fallback to `linux-arm64` where AVX would not be available (`build_common.sh:27–31`).
> - **Source of flags:** `build_common.sh:48–76`; SIMD: `n-body/main.fs:8–20`; YML: `n-body.yml:18`.

---

> **regex-redux — F#**
> - **Execution:** JIT via CLR (.NET 9.0, `dotnet build`). Output: `/tmp/fsharp-regex-redux` shell wrapper. Canonical run: reads from `fasta-25000000.txt` via stdin, extra arg `0`. Test run: same with smaller input.
> - **Concurrency:** Multi-threaded via F# `Async.Parallel`. Ten async computations (one `replaceTask` + nine `regexCount` pattern-match tasks) are composed with `Async.Parallel` + `Async.RunSynchronously` (`regex-redux/main.fs:38–51`). Each async task compiles and runs its own `Regex` instance independently. Thread count: CLR thread pool managed, up to 10 concurrent.
> - **Build/runtime config:** `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`. Uses `System.Text.RegularExpressions.Regex` with `RegexOptions.Compiled` (JIT-compiles regex to IL at runtime, on top of CLR JIT). No external regex library (unlike C/C++ which use PCRE2). `setup_dependencies.sh` called at setup.
> - **Source of flags:** `build_common.sh:48–76`; concurrency: `regex-redux/main.fs:38–51`; YML: `regex-redux.yml:18–19`.

---

> **spectral-norm — F#**
> - **Execution:** JIT via CLR (.NET 9.0, `dotnet build`). Output: `/tmp/fsharp-spectral-norm` shell wrapper. Canonical run: `n=5500`. Test run: `n=500`.
> - **Concurrency:** Multi-threaded via `System.Threading.Tasks.Parallel.For`. The `mult` function uses `Parallel.For(0, v.Length, fun i -> ...)` at `spectral-norm/main.fs:27–39` to parallelise matrix-vector multiplication rows. Called twice per power-iteration step (once for `A*v`, once for `A^T*(A*v)`), 10 total iterations. Thread count: pool-managed, scales with logical CPU count.
> - **Build/runtime config:** `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`. SIMD: uses `System.Runtime.Intrinsics.Vector128<float>` (`F64x2`) with SSE4.1 intrinsics (`Sse41.HorizontalAdd`) and `Vector128` arithmetic (`spectral-norm/main.fs:1–10, 14–17`). Falls back gracefully if SSE4.1 not present (`if Sse41.IsSupported then ... else`). `setup_dependencies.sh` called at setup.
> - **Source of flags:** `build_common.sh:48–76`; concurrency: `spectral-norm/main.fs:27–39` (`Parallel.For`); SIMD: `spectral-norm/main.fs:8–9, 14–17`; YML: `spectral-norm.yml:18`.

---

## Discrepancy log

1. **`fasta.yml` and `mandelbrot.yml` omit `setup_dependencies.sh`** in their `setup-commands`, while binary-trees, fannkuch-redux, k-nucleotide, n-body, regex-redux, and spectral-norm all include it. The `setup_dependencies.sh` pre-restores the `Microsoft.Experimental.Collections` NuGet package. For benchmarks that do not use that package, calling it is harmless but redundant. The omission in fasta and mandelbrot is not harmful (neither uses the package), but the inconsistency is unexplained — `flags.md` does not mention it.
   - Confirmed: `fasta.yml:9` (only `build_in_tmp.sh`); `mandelbrot.yml:9` (only `build_in_tmp.sh`).

2. **`flags.md` states the output is "a native `program` launcher that runs directly"** but `build_common.sh:91–96` shows the launcher is a shell script (`#!/bin/sh\nexec dotnet "$DLL" "$@"`), not a native binary. It runs `dotnet` (the CLR host) with the built DLL. The word "native" in `flags.md` is misleading — the actual execution requires the `dotnet` runtime to be present on `$PATH`. This is structurally different from C# NativeAOT which produces a true standalone binary. No correction needed to the YMLs, but the `flags.md` description is imprecise.

3. **`n-body` uses AVX2 intrinsics (`Vector256<float>`) but `build_common.sh` has an `linux-arm64` fallback RID** (`build_common.sh:29–31`). The `Vector256` + `Avx` code path will compile on ARM64 but the AVX intrinsics will be absent at runtime (AVX is x86-only). The `System.Runtime.Intrinsics.X86.Avx` calls would throw `PlatformNotSupportedException` on ARM64. This is a latent portability bug in the source, though in practice the GMT measurement environment is `linux-x64`.

---

## Summary table row(s)

| Language | Compilation Type | Build Command | Enabling Flags | Concurrency | Notes |
|----------|-----------------|---------------|----------------|-------------|-------|
| F# | JIT via CLR (`dotnet build`, not AOT) | `dotnet build -r linux-x64 -c Release` | `PublishAot=false`, `ImplicitUsings=enable`, `Nullable=enable`, `AllowUnsafeBlocks=true`, `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`, `net9.0` | Per-benchmark (see below) | CLR warmup applies; output is shell wrapper calling `dotnet <dll>`, not a standalone binary |
| F# binary-trees | JIT | — | (shared) | Multi: `Async.Parallel`, 9 tasks (one per depth level), pool-managed | Server GC relevant for parallel tree allocation |
| F# fannkuch-redux | JIT | — | (shared) | Multi: `Async.Parallel`, `ProcessorCount` tasks, scales with CPU | Unsafe NativePtr permutation loop |
| F# fasta | JIT | — | (shared) | Multi: `Task.Run` per block, pool-managed | `ArrayPool` buffer recycling; omits `setup_dependencies.sh` |
| F# k-nucleotide | JIT | — | (shared) + `Microsoft.Experimental.Collections` 1.0.6-e190117-3 | Multi: `Async.Parallel` (7 outer + 4 inner per `count64`), `Array.Parallel.iter` | Most complex concurrency structure; `DictionarySlim` |
| F# mandelbrot | JIT | — | (shared) | Multi: `Parallel.For` across rows, scales with CPU | SIMD: `System.Numerics.Vector<float>`; omits `setup_dependencies.sh` |
| F# n-body | JIT | — | (shared) | Single-threaded | SIMD: `Vector256<float>` + explicit AVX2 intrinsics; AVX not available on ARM64 fallback |
| F# regex-redux | JIT | — | (shared) | Multi: `Async.Parallel`, 10 tasks (9 pattern counts + 1 replace), pool-managed | `Regex(pattern, RegexOptions.Compiled)` — JIT-within-JIT |
| F# spectral-norm | JIT | — | (shared) | Multi: `Parallel.For` across matrix rows, scales with CPU | SIMD: `Vector128<float>` + SSE4.1 with runtime guard |
