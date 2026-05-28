# Rust Benchmark Insights

**Language:** Rust  
**Toolchain:** Rust 1.93 (rustc + cargo, Rust 2021 edition)  
**Docker image:** `rust:1.93-alpine` (all 8 benchmarks)

---

## Per-Benchmark Breakdown

> **Binary-Trees — Rust**
> - Execution: AOT via `cargo build --release --locked --offline` (Rust 1.93, `rust:1.93-alpine`). Binary retained at `/tmp/cargo-target/binary-trees/release/binary-trees`. Run: `binary-trees 21`.
> - Concurrency: **Multi-threaded** via `rayon`. The outer depth loop (`min_depth/2..=max_depth/2`) is parallelised with `.into_par_iter()`, and each call to `inner()` parallelises the iteration count loop with a second `.into_par_iter()` + `.sum()`. Rayon uses a work-stealing thread pool sized to the number of logical CPUs (rayon default; no explicit thread count set in source). No SIMD intrinsics.
> - Build/runtime config: `RUSTFLAGS="-C opt-level=3 -C target-cpu=ivybridge -C codegen-units=1"` (conditional `-L /opt/src/rust-libs` appended when that path exists). Crates: `bumpalo = "3"` (arena allocator), `rayon = "1"` (parallel iterators). Cargo edition 2021.
> - Source of flags: `benchmarks/rust/binary-trees/build_in_tmp.sh:15`, crates at `benchmarks/rust/binary-trees/Cargo.toml:11-12`, concurrency confirmed at `benchmarks/rust/binary-trees/main.rs:43-49,73-80`.

---

> **Fannkuch-Redux — Rust**
> - Execution: AOT via `cargo build --release --locked --offline` (Rust 1.93, `rust:1.93-alpine`). Binary at `/tmp/cargo-target/fannkuch-redux/release/fannkuch-redux`. Run: `fannkuch-redux 12`.
> - Concurrency: **Multi-threaded** via `rayon`. Two nested `.into_par_iter()` calls divide the permutation space: the outer loop over `0..n` and an inner loop over `0..n-1`, each reduced via `.reduce(|| (0,0), ...)`. Rayon uses its default work-stealing thread pool (logical CPU count). **SIMD present**: uses `std::arch::x86_64` intrinsics `_mm_shuffle_epi8` (SSSE3) and `_mm_extract_epi8` (SSE4.1) directly in `reverse_array` and `rotate_array` for in-register permutation of 16-byte arrays; also uses `get::<IMM8>` via `_mm_extract_epi8`.
> - Build/runtime config: `RUSTFLAGS="-C opt-level=3 -C target-cpu=ivybridge -C codegen-units=1"` (conditional `-L /opt/src/rust-libs`). Crates: `rayon = "1"`. No `std::arch` intrinsics declared in Cargo.toml (used from `std`). Cargo edition 2021.
> - Source of flags: `benchmarks/rust/fannkuch-redux/build_in_tmp.sh:15`, crates at `benchmarks/rust/fannkuch-redux/Cargo.toml:11`, SIMD at `benchmarks/rust/fannkuch-redux/main.rs:10-11,36-43,65-72`, rayon at `main.rs:112-150`.
> - Note: `target-cpu=ivybridge` is used here. Ivybridge supports SSSE3 and SSE4.1, so the intrinsics are compatible with the target-cpu setting.

---

> **Fasta — Rust**
> - Execution: AOT via `cargo build --release --locked --offline` (Rust 1.93, `rust:1.93-alpine`). Binary copied to `/tmp/rust-fasta`. Run: `fasta 25000000`.
> - Concurrency: **Multi-threaded** via `std::thread`. The `fasta_random_par` function spawns `num_threads` OS threads (`thread::spawn`) that compete for work using a spin-locked `MyRandom` and a spin-locked `MyStdOut` (both from the `spin` crate's `Mutex`). Thread count = `min(num_cpus::get(), 2)` — capped at 2. **SIMD present**: `gen_from_u32` uses `core::arch::x86_64` SSE2 intrinsics (`_mm_load_si128`, `_mm_cmplt_epi32`, `_mm_sub_epi32`, `_mm_extract_epi32`) when `target_feature = "sse2"` is active; falls back to scalar loop otherwise.
> - Build/runtime config: `RUSTFLAGS="-C opt-level=3 -C target-cpu=native -C codegen-units=1"`. Crates: `num_cpus = "1"` (CPU count), `spin = "0.9"` (spinlock mutex). Cargo edition 2021.
> - Source of flags: `benchmarks/rust/fasta/build_in_tmp.sh:18`, crates at `benchmarks/rust/fasta/Cargo.toml:11-12`, thread count at `benchmarks/rust/fasta/main.rs:260`, SIMD at `main.rs:51-80`, threading at `main.rs:233-251`.

---

> **K-Nucleotide — Rust**
> - Execution: AOT via `cargo build --release --locked --offline` (Rust 1.93, `rust:1.93-alpine`). Binary copied to `/tmp/rust-k-nucleotide`. Run: `k-nucleotide < /tmp/repo/inputs/fasta-2500000.txt`.
> - Concurrency: **Multi-threaded** via `tokio-threadpool`. The `calc` function creates a `ThreadPool` (sized to the Tokio default, which follows the number of logical CPUs) and submits 7 independent frequency-counting tasks as futures using `pool.spawn_handle(lazy(...))`, then waits on them sequentially. Each task calls `freq()` single-threadedly. No SIMD intrinsics in source.
> - Build/runtime config: `RUSTFLAGS="-C opt-level=3 -C target-cpu=native -C codegen-units=1"`. Crates: `futures = "0.1"` (future combinators), `tokio-threadpool = "0.1"` (thread pool executor), `itertools = "0.14"` (sorted_by for output), `num = "0.4"` (numeric traits `FromPrimitive`/`ToPrimitive`), `hashbrown = "0.15"` (hash map). Cargo edition 2021.
> - Source of flags: `benchmarks/rust/k-nucleotide/build_in_tmp.sh:18`, crates at `benchmarks/rust/k-nucleotide/Cargo.toml:11-15`, thread pool at `benchmarks/rust/k-nucleotide/main.rs:159,169-175`.

---

> **Mandelbrot — Rust**
> - Execution: AOT via `cargo build --release --locked --offline` (Rust 1.93, `rust:1.93-alpine`). Binary copied to `/tmp/rust-mandelbrot`. Run: `mandelbrot 16000`.
> - Concurrency: **Multi-threaded** via `rayon`. `rows.par_chunks_mut(size / VLEN).enumerate().for_each(...)` distributes rows across rayon's work-stealing thread pool (logical CPU count, no explicit cap). No `std::arch` SIMD intrinsics; however, the inner loop uses a hand-written `F64x8` struct (8-wide f64 array, `#[repr(align(32))]`) with `impl_binary!` operator overloads — this is a scalar-coded SIMD-friendly structure that LLVM/rustc can auto-vectorize into AVX/AVX2 instructions at `opt-level=3 target-cpu=native`.
> - Build/runtime config: `RUSTFLAGS="-C opt-level=3 -C target-cpu=native -C codegen-units=1"`. Crates: `rayon = "1"`. Cargo edition 2021.
> - Source of flags: `benchmarks/rust/mandelbrot/build_in_tmp.sh:18`, crates at `benchmarks/rust/mandelbrot/Cargo.toml:11`, parallelism at `benchmarks/rust/mandelbrot/main.rs:165`, F64x8 struct at `main.rs:21-88`.

---

> **N-Body — Rust**
> - Execution: AOT via **direct `rustc`** (no Cargo). Compiled with `rustc -C opt-level=3 -C target-cpu=native -C codegen-units=1 main.rs -o /tmp/rust-n-body`. No Cargo.toml exists for this benchmark. Run: `n-body 50000000`.
> - Concurrency: **Single-threaded**. No `rayon`, no `std::thread`, no thread pool. All computation runs on the main thread in a single `advance()` loop. **SIMD present and prominent**: uses `std::arch::x86_64` AVX/AVX2 intrinsics throughout — `_mm256_sub_pd`, `_mm256_mul_pd`, `_mm256_hadd_pd`, `_mm256_permute2f128_pd`, `_mm256_blend_pd`, `_mm256_add_pd`, `_mm256_store_pd`, `_mm256_load_pd`, `_mm256_cvtpd_ps`, `_mm_rsqrt_ps`, `_mm256_cvtps_pd`, `_mm256_set1_pd`, `_mm256_setr_pd`. A custom Newton-Raphson `_mm256_rsqrt_pd` is also implemented. All hot functions (`kernel`, `energy`, `advance`) are `unsafe` blocks exclusively using AVX intrinsics.
> - Build/runtime config: `RUSTFLAGS` equivalent embedded directly in `rustc` command: `-C opt-level=3 -C target-cpu=native -C codegen-units=1`. No crate dependencies (stdlib only). No Cargo.toml.
> - Source of flags: `benchmarks/rust/n-body/build_in_tmp.sh:4-9`, SIMD at `benchmarks/rust/n-body/main.rs:17,24-37,55-96`.

---

> **Regex-Redux — Rust**
> - Execution: AOT via `cargo build --release --locked --offline` (Rust 1.93, `rust:1.93-alpine`). Binary copied to `/tmp/rust-regex-redux`. Run: `regex-redux < /tmp/repo/inputs/fasta-5000000.txt`. Requires host packages `pcre2-dev pkgconf` (installed at setup).
> - Concurrency: **Multi-threaded** via `rayon`. `rayon::scope` spawns 3 parallel tasks: (1) reading stdin and stripping headers, (2) computing substitution sequence length, (3) counting reverse complement variants. Within `count_reverse_complements`, a `variants.into_par_iter()` distributes the 9 regex patterns across rayon's thread pool. Rayon uses its default work-stealing pool (logical CPU count). No `std::arch` SIMD intrinsics in source (PCRE2's own JIT handles pattern matching efficiently via the `pcre2_jit_compile_8`/`pcre2_jit_match_8` FFI path).
> - Build/runtime config: `RUSTFLAGS="-C opt-level=3 -C target-cpu=native -C codegen-units=1"`. Crates: `rayon = "1"`, `libc = "0.2"` (ioctl/FIONREAD for stdin size hint), `pcre2-sys = "0.2"` (raw FFI bindings to libpcre2-8). Cargo edition 2021.
> - Source of flags: `benchmarks/rust/regex-redux/build_in_tmp.sh:18`, crates at `benchmarks/rust/regex-redux/Cargo.toml:11-13`, rayon at `benchmarks/rust/regex-redux/main.rs:320-351,268-275`, pcre2 JIT at `main.rs:107,132`.

---

> **Spectral-Norm — Rust**
> - Execution: AOT via `cargo build --release --locked --offline` (Rust 1.93, `rust:1.93-alpine`). Binary copied to `/tmp/rust-spectral-norm`. Run: `spectral-norm 5500`.
> - Concurrency: **Multi-threaded** via `rayon`. `out.par_iter_mut().enumerate().for_each(...)` in the `mult` function parallelises output vector computation across rayon's work-stealing pool (logical CPU count). **SIMD present**: uses `std::arch::x86_64` SSE2 intrinsics (`_mm_set1_pd`, `_mm_set_pd`, `_mm_storeu_pd`, `_mm_add_pd`, `_mm_mul_pd`, `_mm_div_pd`, `_mm_hadd_pd`) in the `F64x2` struct (SSE3 `_mm_hadd_pd`). The module is conditionally compiled: `#[cfg(all(target_arch = "x86_64", target_feature = "sse2"))]`; without SSE2 it panics.
> - Build/runtime config: `RUSTFLAGS="-C opt-level=3 -C target-cpu=native -C codegen-units=1"`. Crates: `rayon = "1"`. Cargo edition 2021.
> - Source of flags: `benchmarks/rust/spectral-norm/build_in_tmp.sh:18`, crates at `benchmarks/rust/spectral-norm/Cargo.toml:11`, SSE2/SSE3 intrinsics at `benchmarks/rust/spectral-norm/main.rs:14-121`, rayon at `main.rs:85`.

---

## Discrepancy log

1. **`target-cpu` inconsistency — binary-trees and fannkuch-redux use `ivybridge`; all other 6 benchmarks use `native`.**
   - `binary-trees/build_in_tmp.sh:15`: `target-cpu=ivybridge`
   - `fannkuch-redux/build_in_tmp.sh:15`: `target-cpu=ivybridge`
   - All others (`fasta`, `k-nucleotide`, `mandelbrot`, `n-body`, `regex-redux`, `spectral-norm`): `target-cpu=native`
   - Impact: `ivybridge` caps the ISA to Ivy Bridge features (no AVX2, no BMI2, etc.), whereas `native` enables all CPU features of the host. Specifically for `fannkuch-redux`, which uses SSE3/SSE4.1 intrinsics from `std::arch::x86_64`, `ivybridge` does support those features, so correctness is not affected. However, if the measurement host supports AVX2, auto-vectorisation in binary-trees is restricted under `ivybridge`. This inconsistency is real and may slightly penalise binary-trees and fannkuch-redux relative to the other benchmarks.
   - Confirmed: `docs/flags.md:51-52` documents `ivybridge` for both; the `build_in_tmp.sh` files confirm it.

2. **binary-trees `build_in_tmp.sh` includes an optional `-L /opt/src/rust-libs` flag not documented in `docs/flags.md`.**
   - `build_in_tmp.sh:16-18`: `if [ -d /opt/src/rust-libs ]; then RUSTFLAGS_VALUE="$RUSTFLAGS_VALUE -L /opt/src/rust-libs"; fi`
   - Same conditional block is in `fannkuch-redux/build_in_tmp.sh:16-18`. Not present in any other benchmark. Not mentioned in `docs/flags.md`.
   - Impact: low — only takes effect if `/opt/src/rust-libs` exists in the container, which is not set up by the YAML `setup-commands`. Effectively a no-op in standard runs.

3. **binary-trees binary path differs from other benchmarks.**
   - binary-trees and fannkuch-redux binaries remain in the Cargo target directory (`/tmp/cargo-target/<bench>/release/<bench>`); all other cargo-built benchmarks (`fasta`, `k-nucleotide`, `mandelbrot`, `regex-redux`, `spectral-norm`) copy the binary to `/tmp/rust-<bench>`. No functional impact on measurement.

4. **`docs/flags.md` lists `tokio-threadpool` for k-nucleotide but omits `futures = "0.1"` and `num = "0.4"` from the crate list.**
   - `docs/flags.md:54`: lists `futures`, `tokio-threadpool`, `hashbrown`, `itertools`, `num` — this is actually correct and complete. No real discrepancy.

5. **Fasta: `docs/flags.md` documents `num_cpus` and `spin` crates — confirmed correct by `Cargo.toml` and usage in `main.rs`. No discrepancy.**

6. **N-body: no Cargo.toml present in `benchmarks/rust/n-body/`** — consistent with direct `rustc` build; `docs/flags.md:56` correctly notes "Direct rustc, no Cargo". Confirmed.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| Rust (binary-trees) | AOT (cargo/rustc 1.93) | `-C opt-level=3 -C target-cpu=ivybridge -C codegen-units=1` | Multi-threaded; rayon work-stealing pool (logical CPU count) | `bumpalo` arena allocator; **`target-cpu=ivybridge`** (differs from 6 other benchmarks) |
| Rust (fannkuch-redux) | AOT (cargo/rustc 1.93) | `-C opt-level=3 -C target-cpu=ivybridge -C codegen-units=1` | Multi-threaded; rayon (nested par_iter); SIMD: SSE3+SSE4.1 (`_mm_shuffle_epi8`, `_mm_extract_epi8`) | **`target-cpu=ivybridge`** (differs); SSE3/SSE4.1 intrinsics are ivybridge-compatible |
| Rust (fasta) | AOT (cargo/rustc 1.93) | `-C opt-level=3 -C target-cpu=native -C codegen-units=1` | Multi-threaded; std::thread; thread count = min(num_cpus, 2); SIMD: SSE2 (`_mm_load_si128` etc.) | `spin` mutex for RNG/stdout coordination; thread count hard-capped at 2 |
| Rust (k-nucleotide) | AOT (cargo/rustc 1.93) | `-C opt-level=3 -C target-cpu=native -C codegen-units=1` | Multi-threaded; tokio-threadpool (futures 0.1); 7 parallel freq tasks; pool size = logical CPUs | Legacy futures 0.1 + tokio-threadpool 0.1 API; `hashbrown` hash map |
| Rust (mandelbrot) | AOT (cargo/rustc 1.93) | `-C opt-level=3 -C target-cpu=native -C codegen-units=1` | Multi-threaded; rayon (par_chunks_mut); logical CPU count | F64x8 aligned struct enables LLVM auto-vectorization (AVX/AVX2); no explicit intrinsics |
| Rust (n-body) | AOT (direct rustc 1.93, no Cargo) | `-C opt-level=3 -C target-cpu=native -C codegen-units=1` | **Single-threaded**; SIMD: AVX/AVX2 (`_mm256_*` intrinsics throughout) | Only Rust benchmark with no parallelism; most SIMD-intensive; custom `_mm256_rsqrt_pd` |
| Rust (regex-redux) | AOT (cargo/rustc 1.93) | `-C opt-level=3 -C target-cpu=native -C codegen-units=1` | Multi-threaded; rayon scope (3 tasks) + par_iter (9 regex patterns) | PCRE2 JIT via FFI (`pcre2-sys`); `libc` for stdin size hint; `pcre2-dev pkgconf` required |
| Rust (spectral-norm) | AOT (cargo/rustc 1.93) | `-C opt-level=3 -C target-cpu=native -C codegen-units=1` | Multi-threaded; rayon (par_iter_mut); SIMD: SSE2+SSE3 (`_mm_hadd_pd` etc.) | `F64x2` SSE2/SSE3 struct; panics if SSE2 not available; `target_feature="sse2"` required |
