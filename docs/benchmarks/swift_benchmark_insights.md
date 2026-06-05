# Swift Benchmark Insights

**Language:** Swift  
**Swift version:** 6.0.3  
**Docker image:** `swift:6.0.3`  
**Source of image:** all eight `<benchmark>.yml` files, `services.swift-container.image` field

---

## Benchmarks

> **Binary-Trees — Swift**
> - Execution: AOT via `swiftc` (Swift 6.0.3) with `-Ounchecked -wmo`
> - Concurrency: **Multi-threaded** via Grand Central Dispatch (GCD). Two top-level work items are dispatched asynchronously onto a concurrent `workerQueue` (one for the stretch tree, one for the long-lived tree); then a third async block on the same queue spawns one additional async task per depth level, each posting its result to a serial `messageQueue`. All tasks are tracked with a `DispatchGroup`; the main thread blocks on `group.wait()`. Thread count is GCD-managed (scales with available CPUs via the global thread pool).
> - Build/runtime config: `-Ounchecked -wmo`, compiled from `benchmarks/swift/binary-trees/main.swift` to `/tmp/swift-binary-trees`; run with argument `21`.
> - Source of flags: `benchmarks/swift/binary-trees.yml:9`
> - ARC/memory note: Uses reference-type `TreeNode` (`class`), so every node allocation is ARC-managed heap memory. `-Ounchecked` disables ARC retain/release overflow checks. The tree is fully recursive and heap-allocated; expect significant allocation pressure at depth 21.
> - Source concurrency: `benchmarks/swift/binary-trees/main.swift:61–107` (`DispatchGroup`, `workerQueue`, `messageQueue`)

---

> **Fannkuch-Redux — Swift**
> - Execution: AOT via `swiftc` (Swift 6.0.3) with `-Ounchecked -wmo`
> - Concurrency: **Multi-threaded** via `DispatchQueue.concurrentPerform(iterations: ntasks)` (line 151). Work is divided into `ntasks` chunks (derived from `nchunks = 150` at line 27) and dispatched as parallel iterations over GCD's global thread pool. Thread count scales with available CPUs; GCD calibrates the pool to the hardware.
> - Build/runtime config: `-Ounchecked -wmo`, compiled from `benchmarks/swift/fannkuch-redux/main.swift` to `/tmp/swift-fannkuch-redux`; run with argument `12`.
> - Source of flags: `benchmarks/swift/fannkuch-redux.yml:9`
> - Memory note: Each task (`Fannkuch` struct) allocates three `UnsafeMutablePointer<Int>` buffers (`p`, `pp`, `count`) of size `n` via manual `allocate`/`deallocate` — bypassing ARC entirely. The factorials buffer (`fact`) is also manually allocated (`main.swift:19`). `-Ounchecked` skips bounds checking on these raw pointer accesses.
> - Source concurrency: `benchmarks/swift/fannkuch-redux/main.swift:151` (`DispatchQueue.concurrentPerform`)

---

> **Fasta — Swift**
> - Execution: AOT via `swiftc` (Swift 6.0.3) with `-Ounchecked -wmo`
> - Concurrency: **Multi-threaded** via GCD with a producer–consumer pipeline. A serial `pQueue` (Producer) generates random numbers into one of 4 rotating `UnsafeMutablePointer<Int32>` buffers; a concurrent `cQueue` (Consumer) converts raw values to amino acid characters; a serial `wQueue` (Writer) prints output in order. Buffer ownership is coordinated via `DispatchSemaphore` pairs (`pSemaphore`, `wSemaphore`). All tasks tracked with a `DispatchGroup`. The `repeatFasta` function (for the ALU sequence) is single-threaded. Thread count is GCD-managed.
> - Build/runtime config: `-Ounchecked -wmo`, compiled from `benchmarks/swift/fasta/main.swift` to `/tmp/swift-fasta`; run with argument `25000000`.
> - Source of flags: `benchmarks/swift/fasta.yml:9`
> - Memory note: Four pairs of raw `UnsafeMutablePointer<Int32>` / `UnsafeMutablePointer<Int8>` buffers allocated at startup and freed with `defer` (`main.swift:63–78`). The random-number state (`seed`) is a module-level `var` written serially from `pQueue` only, avoiding races.
> - Source concurrency: `benchmarks/swift/fasta/main.swift:82–84` (queue declarations), `173–207` (pipeline dispatch)

---

> **K-Nucleotide — Swift**
> - Execution: AOT via `swiftc` (Swift 6.0.3) with `-Ounchecked -wmo`
> - Concurrency: **Multi-threaded** via `DispatchQueue.concurrentPerform(iterations: ntasks)` inside `getSequenceHash` (line 52), where `ntasks = 8` (line 14, hardcoded). Each of the 8 parallel workers builds a local `[Int:Int]` dictionary for its slice of the sequence, then merges it into a shared dictionary via a serial `mQueue.sync` critical section. Called multiple times (for k=1,2,3,4,6,12,18), always with 8 concurrent tasks. Thread count: GCD global pool, bounded logically by the hardcoded 8 iterations.
> - Build/runtime config: `-Ounchecked -wmo`, compiled from `benchmarks/swift/k-nucleotide/main.swift` to `/tmp/swift-k-nucleotide`; run with stdin from `/tmp/repo/inputs/fasta-25000000.txt` and argument `0`.
> - Source of flags: `benchmarks/swift/k-nucleotide.yml:9`
> - Source concurrency: `benchmarks/swift/k-nucleotide/main.swift:14` (`ntasks = 8`), `52` (`DispatchQueue.concurrentPerform`), `17–18` (queue declarations)

---

> **Mandelbrot — Swift**
> - Execution: AOT via `swiftc` (Swift 6.0.3) with `-Ounchecked -wmo`
> - Concurrency: **Multi-threaded** via `DispatchQueue.concurrentPerform` called twice: once to initialize the `Cr0Array` of pre-computed SIMD8 real-part values (line 43–50), and once to compute each scanline in parallel (line 52–65). Thread count is GCD-managed (scales with CPUs). Output is written directly to `FileHandle.standardOutput` after all lines are computed.
> - SIMD: **Explicit SIMD8<Double>** used throughout. Eight pixels are computed in parallel per SIMD lane per loop iteration (`onepixel` function, line 76–84). Early-exit optimization: if a pixel byte is 0 (all-out), the inner loop checks every 5 iterations whether all 8 points have escaped (line 109–114) and returns early. `-Ounchecked` eliminates overflow traps on integer arithmetic.
> - Build/runtime config: `-Ounchecked -wmo`, compiled from `benchmarks/swift/mandelbrot/main.swift` to `/tmp/swift-mandelbrot`; run with argument `16000`.
> - Source of flags: `benchmarks/swift/mandelbrot.yml:9`
> - Source concurrency/SIMD: `benchmarks/swift/mandelbrot/main.swift:36` (`SIMD8<Double>`), `43` and `52` (`DispatchQueue.concurrentPerform`), `76–84` (`onepixel` with SIMD)

---

> **N-Body — Swift**
> - Execution: AOT via `swiftc` (Swift 6.0.3) with `-Ounchecked -wmo`
> - Concurrency: **Single-threaded**. No GCD, no `Thread`, no `concurrentPerform`. The simulation loop (`for _ in 0..<n { system.step(dt: 0.01) }`, line 202–204) is purely sequential. The `step` method iterates over all planet pairs with nested loops.
> - SIMD: **SIMD4<Double>** used for position and velocity vectors in `step` and `energy` methods (lines 96–115). On Linux, the module imports `Foundation` only; the `dot` function is provided inline (lines 15–17) as `(a * b).sum()`. On non-Linux, Swift's `simd` framework is imported (line 13). Struct `Body` uses a `Vec4` tuple (`(x,y,z,w): Double`) as its storage type, wrapped into `SIMD4<Double>` at each arithmetic step. `@frozen`, `@usableFromInline`, `@inline(__always)` annotations encourage aggressive inlining.
> - Build/runtime config: `-Ounchecked -wmo`, compiled from `benchmarks/swift/n-body/main.swift` to `/tmp/nbody.swift-3.swift_run`; run with argument `50000000`.
> - Source of flags: `benchmarks/swift/n-body.yml:9`
> - Note on binary name: the output binary is named `nbody.swift-3.swift_run` (matching a CLBG naming convention), unlike the pattern used by most other Swift benchmarks.
> - Source concurrency: `benchmarks/swift/n-body/main.swift:200–205` (no concurrency primitives present); SIMD: lines `11–17`, `96–116`

---

> **Regex-Redux — Swift**
> - Execution: AOT via `swiftc` (Swift 6.0.3) with `-Ounchecked -wmo`
> - Concurrency: **Multi-threaded** via `DispatchQueue.global().async` + `DispatchGroup`. One background task computes the replacement result length (line 30–42) concurrently with nine tasks (one per variant pattern, lines 58–65) that count pattern matches in parallel. All tasks are joined via `group.wait()` (line 67). Thread count: GCD global pool, up to 10 concurrent tasks.
> - Regex engine: uses **`NSRegularExpression`** (ICU-based; part of Foundation on Linux). No PCRE2. Sequence stripping is done with `replacingOccurrences(of:options:.regularExpression)` (line 20–21) on the main thread before dispatching concurrent work.
> - Build/runtime config: `-Ounchecked -wmo`, compiled from `benchmarks/swift/regex-redux/main.swift` to `/tmp/regexredux.swift-4.swift_run`; run with stdin from `/tmp/repo/inputs/fasta-25000000.txt` and argument `0`.
> - Source of flags: `benchmarks/swift/regex-redux.yml:9`
> - Source concurrency: `benchmarks/swift/regex-redux/main.swift:27–67` (`DispatchGroup`, `DispatchQueue.global().async`)

---

> **Spectral-Norm — Swift**
> - Execution: AOT via `swiftc` (Swift 6.0.3) with `-Ounchecked -wmo`
> - Concurrency: **Multi-threaded** via `DispatchQueue.concurrentPerform(iterations: n)` inside both `multiplyAv` (line 26) and `multiplyAtv` (line 40). Each row of the matrix–vector product is computed as an independent concurrent task. Thread count is GCD-managed (scales with CPUs). Note: the author's comment (line 31–33) acknowledges that unprotected writes to `Av[i]` / `Atv[i]` could be hazardous in general, but is safe here because each task writes to a distinct index.
> - Build/runtime config: `-Ounchecked -wmo`, compiled from `benchmarks/swift/spectral-norm/main.swift` to `/tmp/spectralnorm.swift-3.swift_run`; run with argument `5500`.
> - Source of flags: `benchmarks/swift/spectral-norm.yml:9`
> - Source concurrency: `benchmarks/swift/spectral-norm/main.swift:26` and `40` (`DispatchQueue.concurrentPerform`)

---

## Discrepancy log

- **flags.md says `-Ounchecked -wmo` applies to all benchmarks** — confirmed correct for all 8 benchmarks. Each YAML's `setup-commands` uses exactly these two flags and no others. Source: each `<benchmark>.yml:9`.
- **flags.md has no per-benchmark Swift table** — consistent with reality; all 8 benchmarks share identical flags.
- **N-body binary name** (`nbody.swift-3.swift_run`) diverges from the naming convention used by all other Swift benchmarks (`/tmp/swift-<benchmark>` or `spectralnorm.swift-3.swift_run` / `regexredux.swift-4.swift_run`). Three benchmarks (n-body, regex-redux, spectral-norm) use CLBG-derived names with numeric suffixes; five use the cleaner `swift-<benchmark>` pattern. This is a naming inconsistency across benchmarks but has no effect on correctness or performance.
- **Regex-redux uses NSRegularExpression (ICU), not PCRE2** — the other CLBG reference implementations (C, C++, Rust, Java) link against `libpcre2`. The Swift implementation relies on Foundation's `NSRegularExpression`, which uses the ICU regex engine. This is a material implementation difference that could affect both runtime and energy measurements.
- **Fasta `randomFasta` has a data race potential on `seed`** — `seed` is a module-level `var` read and written inside `genRandom`, which is called from both the serial `pQueue` (main loop body) and directly on the main thread (remainder, line 208). In practice the `group.wait()` at line 207 ensures these calls do not overlap, so no actual race occurs at runtime.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| Swift | AOT (`swiftc`) | `-Ounchecked -wmo` | Multi-threaded (GCD) for 7 of 8 benchmarks; single-threaded for n-body | All benchmarks: `swift:6.0.3` image, same flags. Concurrency via `DispatchQueue.concurrentPerform` (fannkuch-redux, k-nucleotide, mandelbrot, spectral-norm), GCD async+DispatchGroup (binary-trees, fasta, regex-redux), or none (n-body). SIMD8<Double> in mandelbrot; SIMD4<Double> in n-body. Regex-redux uses NSRegularExpression/ICU instead of PCRE2. ARC reference-type allocation in binary-trees; manual `UnsafeMutablePointer` memory in fannkuch-redux and fasta. |
