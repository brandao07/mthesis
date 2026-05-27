# Haskell Benchmark Insights

**Language:** Haskell  
**Compiler:** GHC 9.10.1 (AOT, native code via LLVM backend)  
**Image:** `haskell:9.10.1` (all 8 benchmarks)  
**LLVM backend:** `-fllvm`; LLVM toolchain (opt/llc/clang) installed at setup time by probing `llvm-15`, then `llvm-14`, then `llvm-13` via apt.  
**Base compile flags (all benchmarks):** `-O2 -XBangPatterns -fllvm -threaded -rtsopts`  
**Base RTS flags (all benchmarks):** `+RTS -N4 -RTS` (4 OS threads fixed; does NOT scale with host CPU count)

---

## Per-Benchmark Breakdown

---

> **Binary-Trees — Haskell**
> - **Execution:** AOT via `ghc` 9.10.1 (LLVM backend). Compile flags: `-O2 -XBangPatterns -fllvm -fno-cse -package ghc-compact -threaded -rtsopts`. Image `haskell:9.10.1`.
> - **Concurrency:** Multi-threaded. `-threaded -N4` RTS = up to 4 parallel OS threads. Source actively uses parallelism via `Control.Parallel.Strategies` (`rpar`, `rseq`, `parList`): `makePar4` builds tree subtrees in parallel using `rpar` (lines 95–106), `makePar2` parallellises 2 subtrees (lines 109–116), `checkPar4` traverses 4 sub-trees in parallel (lines 72–83), and the main depth-iteration list is evaluated via `parList` (lines 43–44). The `-N4` threads are genuinely utilized.
> - **Build/runtime config:**
>   - Cabal deps installed: `parallel` (`cabal install --lib parallel`)
>   - `ghc-compact` is a GHC bundled package, used via `-package ghc-compact`
>   - `-fno-cse`: disables common sub-expression elimination (necessary for correct tree allocation semantics)
>   - RTS: `+RTS -N4 -K128M -H -RTS` — 4 threads, 128 MB stack limit, initial heap from OS (size determined by RTS)
>   - Benchmark input: `21` (measure), `6` (test)
> - **Source of flags:** `binary-trees.yml:14` (compile), `binary-trees.yml:22` (RTS)

---

> **Fannkuch-Redux — Haskell**
> - **Execution:** AOT via `ghc` 9.10.1 (LLVM backend). Compile flags: `-O2 -XBangPatterns -fllvm -XScopedTypeVariables -threaded -rtsopts`. Image `haskell:9.10.1`.
> - **Concurrency:** Multi-threaded at the RTS level (`-threaded -N4`). Source uses `Control.Concurrent.forkIO` to split the permutation space into 4 equal chunks and process each in a parallel IO thread (lines 98–103: `forM [0,bk..fact-1] $ \ix -> forkIO ...`). Results are synchronised via `MVar`s. The 4 `forkIO` workers genuinely execute in parallel under `-N4`. No `Control.Parallel` or `par`/`rpar` used; concurrency is explicit via the `Control.Concurrent` API.
> - **Build/runtime config:**
>   - No extra cabal deps (no `cabal install` step)
>   - `-XScopedTypeVariables`: enables scoped type variables
>   - RTS: `+RTS -N4 -RTS` — 4 threads, no extra heap/stack limits
>   - Benchmark input: `12` (measure), `6` (test)
> - **Source of flags:** `fannkuch-redux.yml:12` (compile), `fannkuch-redux.yml:20` (RTS)

---

> **Fasta — Haskell**
> - **Execution:** AOT via `ghc` 9.10.1 (LLVM backend). Compile flags: `-O2 -XBangPatterns -fllvm -XStrict -threaded -rtsopts`. Image `haskell:9.10.1`.
> - **Concurrency:** Multi-threaded at the RTS level (`-threaded -N4`). Source uses `Control.Concurrent.forkIO` and `MVar`-based synchronisation to pipeline random FASTA generation across `workers = 4` threads (line 134: `workers = 4`). The `worker` function (lines 57–73) runs concurrently; threads coordinate on a shared `lock` MVar. The `printRandomFasta` function (lines 99–108) forks all workers and waits on a `finish` MVar. Parallelism is real and tied to the 4-thread RTS.
> - **Build/runtime config:**
>   - No extra cabal deps (no `cabal install` step)
>   - `-XStrict`: makes all bindings strict by default (removes lazy thunk overhead)
>   - Uses `Data.Massiv.Array` (massiv) — **note:** `massiv` is not installed via a `cabal install` step in the YAML. It is a third-party library. This will resolve only if it is bundled with the `haskell:9.10.1` image or cabal global cache; this is a potential fragility.
>   - RTS: `+RTS -N4 -RTS` — 4 threads, no extra heap/stack limits
>   - Benchmark input: `25000000` (measure), `100` (test)
> - **Source of flags:** `fasta.yml:12` (compile), `fasta.yml:20` (RTS)

---

> **K-Nucleotide — Haskell**
> - **Execution:** AOT via `ghc` 9.10.1 (LLVM backend). Compile flags: `-O2 -XBangPatterns -fllvm -funbox-strict-fields -XScopedTypeVariables -package hashable -package unordered-containers -package pvar -package ghc-compact -threaded -rtsopts`. Image `haskell:9.10.1`.
> - **Concurrency:** Multi-threaded at the RTS level (`-threaded -N4`). Source uses `Control.Parallel.Strategies` (`rpar`, `runEval`, `mapM`) to parallelize both occurrence counting and frequency computation. `calcOcc` (line 150–151) uses `runEval $ mapM (rpar . threadWorkOcc ...) threads` where `threads = [0..63]` — 64 work items executed in parallel sparks. Similarly `calcFreq` (lines 153–161) uses `runEval $ mapM (rpar . threadWorkFreq len) threads`. The `-N4` threads pick up sparks from the spark pool, so up to 4 OS threads run concurrently at any time despite 64 work units.
> - **Build/runtime config:**
>   - Cabal deps installed: `parallel hashable hashtables containers bytestring unordered-containers pvar`
>   - `-funbox-strict-fields`: unboxes strict record fields for tighter memory layout
>   - `-XScopedTypeVariables`: enables scoped type variables
>   - `-package ghc-compact`: referenced in compile flags but `ghc-compact` package is NOT used in the source (`main.hs` does not import `GHC.Compact`). This is a stale flag (no effect; compile succeeds because the package exists).
>   - RTS: `+RTS -N4 -K2048M -RTS` — 4 threads, 2048 MB stack limit (deep recursion in `countOccurrences`/`go`)
>   - Benchmark input: `< /tmp/repo/inputs/fasta-2500000.txt` (measure), `< /tmp/repo/inputs/fasta-100.txt` (test)
> - **Source of flags:** `k-nucleotide.yml:14` (compile), `k-nucleotide.yml:23` (RTS)

---

> **Mandelbrot — Haskell**
> - **Execution:** AOT via `ghc` 9.10.1 (LLVM backend). Compile flags: `-fllvm -O2 -XBangPatterns -threaded -rtsopts -XMagicHash -XUnboxedTuples`. Image `haskell:9.10.1`. Note: flag order in this benchmark reverses `-fllvm` and `-O2` vs. other benchmarks (no semantic difference).
> - **Concurrency:** Multi-threaded. `-threaded -N4` RTS = 4 OS threads. Source uses low-level `GHC.IO` primitives: `fork#` (lines 179, 211) spawns 4 explicit worker threads (lines 242–249: `worker s` called 4 times, each thread joined via `takeMVar# thread{0..3}`). Workers pull row chunks from a shared `MVar`-based work queue (lines 182–206 and 210–237). This is genuine 4-thread parallelism via `fork#` (the primitive underlying `forkIO`). Also uses `DoubleX2#` SIMD vector primitives (e.g. `timesDoubleX2#`, `plusDoubleX2#`) for 8-pixels-at-a-time computation (`mand8`) and 64-pixels-at-a-time batching (`mand64`) when width is a multiple of 64. Extensions `-XMagicHash` and `-XUnboxedTuples` are required for these GHC primops.
> - **Build/runtime config:**
>   - No extra cabal deps (no `cabal install` step)
>   - `-XMagicHash`: enables `#`-suffixed unboxed literals and types (GHC primops)
>   - `-XUnboxedTuples`: enables `(# ... #)` unboxed tuple syntax (used extensively for SIMD and low-level state passing)
>   - RTS: `+RTS -N4 -RTS` — 4 threads, no extra heap/stack limits
>   - Benchmark input: `16000` (measure), `160` (test)
> - **Source of flags:** `mandelbrot.yml:12` (compile), `mandelbrot.yml:20` (RTS)

---

> **N-Body — Haskell**
> - **Execution:** AOT via `ghc` 9.10.1 (LLVM backend). Compile flags: `-O2 -XBangPatterns -fllvm -threaded -rtsopts`. Image `haskell:9.10.1`.
> - **Concurrency:** Single-threaded computation despite `-threaded -N4` RTS. Source contains no parallelism primitives: no `forkIO`, no `Control.Parallel`, no `async`, no sparks. The entire simulation (`advance`, `energy`, `run`) is a strict sequential loop over 5 planets using `Foreign.Storable`-backed mutable memory. The `-N4` flag reserves 4 RTS capabilities but only one is ever used.
> - **Build/runtime config:**
>   - No extra cabal deps (no `cabal install` step)
>   - Base flags only: `-O2 -XBangPatterns -fllvm -threaded -rtsopts`
>   - Uses `Foreign.Ptr` / `Foreign.Storable` for manual memory layout of `Planet` structs (C-style AoS layout, 8 doubles per planet = 64 bytes)
>   - RTS: `+RTS -N4 -RTS` — 4 threads reserved but unused; no extra heap/stack limits
>   - Benchmark input: `50000000` (measure), `500` (test)
> - **Source of flags:** `n-body.yml:12` (compile), `n-body.yml:20` (RTS)

---

> **Regex-Redux — Haskell**
> - **Execution:** AOT via `ghc` 9.10.1 (LLVM backend). Compile flags: `-O2 -XBangPatterns -fllvm -XForeignFunctionInterface -XCApiFFI -optc "-DPCRE2_CODE_UNIT_WIDTH=8" -threaded -rtsopts`, linked with `-lpcre2-8`. Image `haskell:9.10.1`.
> - **Concurrency:** Multi-threaded. `-threaded -N4` RTS = 4 OS threads. Source uses both `forkIO` and `forkOn`: the replacement pass is forked explicitly to capability 0 via `forkOn 0` (line 221) to avoid scheduler disruption; the 9 count-pattern threads are each forked with `forkIO` (line 258: `for_ ... forkIO`). Count threads run concurrently (each compiles and JIT-executes its own PCRE2 regex), serialising only output via a chained MVar token-passing scheme (lines 286–291). The replacement pass runs in parallel with counting. Genuine multi-threaded use.
> - **Build/runtime config:**
>   - Cabal deps installed: `vector` (`cabal install --lib vector`)
>   - `libpcre2-dev` installed as part of the LLVM apt step (same `setup-commands` block)
>   - `-XForeignFunctionInterface` + `-XCApiFFI`: enables FFI and C API imports for PCRE2
>   - `-optc "-DPCRE2_CODE_UNIT_WIDTH=8"`: passed to the C compiler to configure PCRE2 for 8-bit character units
>   - `-lpcre2-8`: links the PCRE2 native library
>   - Uses PCRE2 JIT (`c_pcre2_jit_compile`, `c_pcre2_jit_match` — line 40 marked `unsafe` for extra FFI performance)
>   - RTS: `+RTS -N4 -H250M -RTS` — 4 threads, 250 MB initial heap allocation hint
>   - Benchmark input: `< /tmp/repo/inputs/fasta-5000000.txt` (measure), `< /tmp/repo/inputs/fasta-100.txt` (test)
> - **Source of flags:** `regex-redux.yml:14` (compile), `regex-redux.yml:23` (RTS)

---

> **Spectral-Norm — Haskell**
> - **Execution:** AOT via `ghc` 9.10.1 (LLVM backend). Compile flags: `-O2 -XBangPatterns -fllvm -XMagicHash -threaded -rtsopts`. Image `haskell:9.10.1`.
> - **Concurrency:** Multi-threaded. `-threaded -N4` RTS = 4 OS threads. Source explicitly uses `GHC.Conc.numCapabilities` to query the RTS capability count at runtime and chunks the work accordingly (line 67: `let chunk = (n + numCapabilities - 1) \`quotInt\` numCapabilities`). Worker threads are spawned with `forkIO` (line 78) and synchronised via a custom `CyclicBarrier` (lines 49–63) backed by `MVar`s. This means the degree of parallelism dynamically matches the number of RTS capabilities, so under `-N4` the work is split into 4 chunks. Parallelism is genuine and adaptive to `-N`.
> - **Build/runtime config:**
>   - No extra cabal deps (no `cabal install` step)
>   - `-XMagicHash`: enables unboxed primop types (used in `aij` for manual unboxing of `Int#`, line 108)
>   - Uses `Foreign.Marshal.Array` for mutable `Ptr Double` arrays (C-style manual allocation)
>   - RTS: `+RTS -N4 -RTS` — 4 threads, no extra heap/stack limits
>   - Benchmark input: `5500` (measure), `500` (test)
> - **Source of flags:** `spectral-norm.yml:12` (compile), `spectral-norm.yml:20` (RTS)

---

## Discrepancy log

1. **K-Nucleotide: stale `-package ghc-compact` flag.** `k-nucleotide.yml:14` passes `-package ghc-compact` to the compiler, but `k-nucleotide/main.hs` does not import or use `GHC.Compact` anywhere. The `flags.md` Haskell table also lists `-package ghc-compact` for k-nucleotide. This is a harmless no-op flag (the package exists so GHC does not error) but it is misleading.

2. **Fasta: `massiv` library not explicitly installed.** `fasta/main.hs` imports `Data.Massiv.Array.Mutable`, `Data.Massiv.Array.Unsafe`, and `Data.Massiv.Array` (lines 6–8). However, the `fasta.yml` setup-commands include no `cabal install --lib massiv` step (unlike binary-trees which installs `parallel`, or k-nucleotide which installs `hashable` etc.). The benchmark relies on `massiv` being pre-installed in the `haskell:9.10.1` Docker image or in a cached cabal store. `flags.md` does not mention this dependency for fasta. This is a documentation gap and a potential portability risk.

3. **`flags.md` lists `parallel` as a cabal dep for k-nucleotide** (`flags.md:98`: "Requires `parallel`, `hashable`, ..."). The `k-nucleotide.yml:12` cabal install command does install `parallel`. However, `k-nucleotide/main.hs` uses only `Control.Parallel.Strategies` (line 20), which is indeed from the `parallel` package, so the dep is needed — but note it is not passed as a `-package parallel` flag to GHC (only `-package hashable -package unordered-containers -package pvar -package ghc-compact` are explicit). GHC finds `parallel` via the cabal lib db without an explicit `-package` flag, which is fine.

4. **N-Body: `-N4` is overhead with no benefit.** Source is fully sequential with no parallelism primitives. The `-threaded` flag adds GHC parallel RTS overhead (lock contention on capability scheduling, GC synchronisation) with no computational benefit. This should be noted when comparing n-body energy results.

5. **No `build_in_tmp.sh` scripts exist for Haskell.** The task description anticipated separate `build_in_tmp.sh` shell scripts per benchmark, but all Haskell build logic is inlined as `setup-commands` in the YAML files. This differs from languages like Rust and C which use `build_in_tmp.sh`.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| Haskell (binary-trees) | AOT via GHC 9.10.1 + LLVM backend | `-O2 -XBangPatterns -fllvm -fno-cse -package ghc-compact -threaded -rtsopts` | Parallel RTS `-N4`; source uses `Control.Parallel.Strategies` (`rpar`/`rseq`/`parList`) for genuine 4-thread tree construction and traversal | RTS: `-K128M -H`; cabal: `parallel` |
| Haskell (fannkuch-redux) | AOT via GHC 9.10.1 + LLVM backend | `-O2 -XBangPatterns -fllvm -XScopedTypeVariables -threaded -rtsopts` | Parallel RTS `-N4`; source uses `forkIO` + `MVar` to split permutation space into 4 parallel workers | No cabal deps |
| Haskell (fasta) | AOT via GHC 9.10.1 + LLVM backend | `-O2 -XBangPatterns -fllvm -XStrict -threaded -rtsopts` | Parallel RTS `-N4`; source uses `forkIO` + `MVar` pipeline with `workers = 4` threads for random FASTA generation | `massiv` dep not explicitly installed (potential fragility) |
| Haskell (k-nucleotide) | AOT via GHC 9.10.1 + LLVM backend | `-O2 -XBangPatterns -fllvm -funbox-strict-fields -XScopedTypeVariables -package hashable -package unordered-containers -package pvar -package ghc-compact -threaded -rtsopts` | Parallel RTS `-N4`; source uses `Control.Parallel.Strategies` (`rpar` via `runEval`/`mapM`) with 64 sparks consumed by 4 OS threads | RTS: `-K2048M`; cabal: `parallel hashable hashtables containers bytestring unordered-containers pvar`; stale `-package ghc-compact` flag |
| Haskell (mandelbrot) | AOT via GHC 9.10.1 + LLVM backend | `-fllvm -O2 -XBangPatterns -threaded -rtsopts -XMagicHash -XUnboxedTuples` | Parallel RTS `-N4`; source uses `fork#` primitive to spawn 4 explicit worker threads with MVar-based work queue; also uses `DoubleX2#` SIMD vector primops | No cabal deps; SIMD via GHC primops |
| Haskell (n-body) | AOT via GHC 9.10.1 + LLVM backend | `-O2 -XBangPatterns -fllvm -threaded -rtsopts` | Single-threaded computation; `-N4` reserves 4 RTS capabilities but source has no parallelism primitives (`forkIO`/`par`/etc. absent) | No cabal deps; uses Foreign.Storable for C-style Planet struct layout; `-threaded` adds overhead without benefit |
| Haskell (regex-redux) | AOT via GHC 9.10.1 + LLVM backend | `-O2 -XBangPatterns -fllvm -XForeignFunctionInterface -XCApiFFI -optc "-DPCRE2_CODE_UNIT_WIDTH=8" -threaded -rtsopts -lpcre2-8` | Parallel RTS `-N4`; source uses `forkOn 0` for replacement pass + `forkIO` for 9 count-pattern threads; concurrent PCRE2 JIT regex matching | RTS: `-H250M`; cabal: `vector`; links `libpcre2-dev`; uses PCRE2 JIT (`unsafe` FFI call) |
| Haskell (spectral-norm) | AOT via GHC 9.10.1 + LLVM backend | `-O2 -XBangPatterns -fllvm -XMagicHash -threaded -rtsopts` | Parallel RTS `-N4`; source uses `forkIO` + custom `CyclicBarrier`; chunk size computed from `numCapabilities` so parallelism adapts to `-N4` | No cabal deps; uses `Foreign.Marshal.Array` for `Ptr Double` arrays |
