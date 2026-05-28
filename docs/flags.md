# Flags

Documents the compiler flags and build settings used for each language's benchmark YAMLs. Flags are derived from the CLBG reference implementations, adapted for the Docker environment (`-march=ivybridge` → `-march=native`; library installs via `apt-get`/`apk`/`opam` where needed).

---

## C

Compiler: `gcc`

| Benchmark      | Flags                                                                                    | Notes                                      |
|----------------|------------------------------------------------------------------------------------------|--------------------------------------------|
| binary-trees   | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp -I/usr/include/apr-1.0 -lapr-1` | Requires `libapr1-dev`                |
| fannkuch-redux | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -pthread`                            | Uses pthreads, not OpenMP; 4 threads hardcoded |
| fasta          | `-pipe -Wall -O3 -fomit-frame-pointer -march=native`                                    |                                            |
| k-nucleotide   | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp`                           | `khash.h` is bundled in benchmark dir      |
| mandelbrot     | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -mno-fma -fno-finite-math-only -fopenmp` |                                       |
| n-body         | `-pipe -Wall -O3 -fomit-frame-pointer -march=native`                                    |                                            |
| regex-redux    | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp -lpcre2-8`                 | PCRE2 bundled in `gcc:15.2.0` image; `pcre2.h` header bundled in benchmark dir; no explicit install |
| spectral-norm  | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp -lm`                       |                                            |

---

## C++

Compiler: `g++`

Only binary-trees, fasta, and regex-redux install `libboost-dev` in `setup-commands`. Fannkuch-redux, k-nucleotide, mandelbrot, n-body, and spectral-norm have no apt-get install step.

| Benchmark      | Flags                                                                              | Notes                                        |
|----------------|------------------------------------------------------------------------------------|----------------------------------------------|
| binary-trees   | `-pipe -O3 -fomit-frame-pointer -march=native -std=gnu++17 -ltbb`                 | Requires `libtbb-dev libboost-dev`; uses `<execution>` and boost headers |
| fannkuch-redux | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -fopenmp`                |                                              |
| fasta          | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -lpthread`               | Requires `libboost-dev`; thread count capped at 2 (`NUM_THREADS = 2`) |
| k-nucleotide   | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -lpthread`               | 4 threads hardcoded (`Cfg::thread_count = 4`) |
| mandelbrot     | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -mno-fma -pthread`       | Uses `<thread>`, not OpenMP                  |
| n-body         | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17`                         |                                              |
| regex-redux    | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -lpcre2-8 -lpthread`     | Requires `libboost-dev`; PCRE2 bundled in base `gcc:15.2.0` image |
| spectral-norm  | `-pipe -O3 -fomit-frame-pointer -march=native -fopenmp`                            | No `-std` flag (only C++ benchmark without explicit standard) |

---

## Rust

Build system: `cargo` (most benchmarks) or direct `rustc` (n-body).

`RUSTFLAGS` are set in each benchmark's `build_in_tmp.sh`.

| Benchmark      | RUSTFLAGS / command                                                   | Notes                                          |
|----------------|-----------------------------------------------------------------------|------------------------------------------------|
| binary-trees   | `-C opt-level=3 -C target-cpu=ivybridge -C codegen-units=1`         | `bumpalo`, `rayon` crates                      |
| fannkuch-redux | `-C opt-level=3 -C target-cpu=ivybridge -C codegen-units=1`         | `rayon` crate; SSE3/SSE4.1 SIMD               |
| fasta          | `-C opt-level=3 -C target-cpu=native -C codegen-units=1`            | `num_cpus`, `spin` crates                      |
| k-nucleotide   | `-C opt-level=3 -C target-cpu=native -C codegen-units=1`            | `futures`, `tokio-threadpool`, `hashbrown`, `itertools`, `num` crates |
| mandelbrot     | `-C opt-level=3 -C target-cpu=native -C codegen-units=1`            | `rayon` crate                                  |
| n-body         | `rustc -C opt-level=3 -C target-cpu=native -C codegen-units=1`      | Direct rustc, no Cargo; SIMD (AVX/AVX2)       |
| regex-redux    | `-C opt-level=3 -C target-cpu=native -C codegen-units=1`            | `rayon`, `libc`, `pcre2-sys` crates; requires `pcre2-dev pkgconf` |
| spectral-norm  | `-C opt-level=3 -C target-cpu=native -C codegen-units=1`            | `rayon` crate; SIMD (SSE2/SSE3)               |

Note: binary-trees and fannkuch-redux use `target-cpu=ivybridge`; all other 6 benchmarks use `target-cpu=native`.

---

## Go

Build system: `go build`

No extra build flags. The Go toolchain's default release build is used for all benchmarks.

`GOMAXPROCS` is set explicitly in several benchmarks (not the Go runtime default):
- `fannkuch-redux`: hardcoded `GOMAXPROCS(4)`
- `fasta`, `regex-redux`: `GOMAXPROCS(runtime.NumCPU())`
- `mandelbrot`, `spectral-norm`: `GOMAXPROCS(runtime.NumCPU() * 2)`
- `binary-trees`, `k-nucleotide`, `n-body`: use Go runtime default (= NumCPU)

`regex-redux` is the only benchmark that uses a Go module and CGO: it fetches `github.com/GRbit/go-pcre@v1.0.0` and links against `libpcre` (`apk add gcc musl-dev pcre-dev`). All other benchmarks compile a single `main.go` file with no external dependencies.

---

## Java (GraalVM AOT)

Steps: `javac` → `native-image`

`native-image` base flags: `-O3 -march=native`. GC: `--gc=G1` (with fallback to `--gc=serial`) for all benchmarks **except binary-trees**, which uses no GC flag (matches CLBG).

| Benchmark      | Extra native-image flags                                                                                                                                                          | Extra notes                                                                                              |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| binary-trees   | _(none — no `--gc` flag per CLBG)_                                                                                                                                               |                                                                                                          |
| k-nucleotide   |                                                                                                                                                                                   | Requires `fastutil-8.3.1.jar` (downloaded at setup)                                                     |
| regex-redux    | `-H:+UnlockExperimentalVMOptions -H:+ForeignAPISupport --enable-native-access=ALL-UNNAMED --features=ForeignRegistrationFeature -Djava.library.path=<pcre2-lib-dir>`             | `build_in_tmp.sh` downloads jextract-22 (build 6-47), installs `libpcre2-dev`/`pcre2-devel`, generates `jextract_pcre2` bindings; PCRE2 lib path resolved dynamically via `find` at build time |
| all others     |                                                                                                                                                                                   |                                                                                                          |

---

## Haskell

Compiler: `ghc`

All benchmarks use `-fllvm` (LLVM backend) and install LLVM/Clang via a version-probing apt script (tries llvm-15, 14, 13). Base flags: `-O2 -XBangPatterns -fllvm -threaded -rtsopts`.

Runtime flags: `+RTS -N4` (4 threads) on all benchmarks; some add heap/stack limits.

| Benchmark      | Extra compile flags                                                                                                          | Extra runtime flags | Notes                                                                                 |
|----------------|------------------------------------------------------------------------------------------------------------------------------|---------------------|---------------------------------------------------------------------------------------|
| binary-trees   | `-fno-cse -package ghc-compact`                                                                                             | `-K128M -H`         | Requires `parallel` (cabal); `ghc-compact` bundled with GHC                          |
| fannkuch-redux | `-XScopedTypeVariables`                                                                                                      |                     |                                                                                       |
| fasta          | `-XStrict`                                                                                                                   |                     | Requires `massiv` (cabal)                                                               |
| k-nucleotide   | `-funbox-strict-fields -XScopedTypeVariables -package hashable -package unordered-containers -package pvar -package ghc-compact` | `-K2048M`       | Requires `parallel`, `hashable`, `hashtables`, `containers`, `bytestring`, `unordered-containers`, `pvar` (cabal); `-package ghc-compact` is stale (not used in source) |
| mandelbrot     | `-XMagicHash -XUnboxedTuples`                                                                                                |                     |                                                                                       |
| n-body         | (base only)                                                                                                                  |                     | Source is fully sequential; `-N4` adds RTS overhead with no computational benefit     |
| regex-redux    | `-XForeignFunctionInterface -XCApiFFI -optc "-DPCRE2_CODE_UNIT_WIDTH=8" -lpcre2-8`                                          | `-H250M`            | Requires `libpcre2-dev` (bundled in LLVM install step); `vector` (cabal)              |
| spectral-norm  | `-XMagicHash`                                                                                                                |                     |                                                                                       |

---

## OCaml

Compiler: `ocamlopt` (via `opam exec`); regex-redux uses `ocamlfind ocamlopt`

Flags (all benchmarks): `-noassert -unsafe -fPIC -nodynlink -inline 100 -O3 -ccopt -march=native`

| Benchmark      | Extra flags / notes                                                         |
|----------------|-----------------------------------------------------------------------------|
| binary-trees   | `-I +unix unix.cmxa`                                                        |
| fannkuch-redux | `-I +unix unix.cmxa`                                                        |
| fasta          | `-I +unix unix.cmxa`                                                        |
| k-nucleotide   | `-I +unix unix.cmxa`                                                        |
| mandelbrot     | `-I +unix unix.cmxa`                                                        |
| n-body         | _(no `-I +unix unix.cmxa`)_                                                 |
| regex-redux    | _(no `-I +unix unix.cmxa`)_; uses `ocamlfind`; links `re` or `re.pcre` (pure-OCaml regex engine, not the C PCRE2 library) |
| spectral-norm  | `-I +unix unix.cmxa`                                                        |

---

## C# (.NET AOT)

Build system: `dotnet publish` (AOT via NativeAOT)

All benchmarks share `build_common.sh` which generates a `.csproj` and publishes with:

- `PublishAot=true`
- `OptimizationPreference=Speed`
- `IlcInstructionSet=native`
- `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`
- Target framework: `net9.0`
- `AllowUnsafeBlocks=true`

All benchmarks share base project settings. Exception: k-nucleotide adds `Microsoft.Experimental.Collections` (1.0.6-e190117-3) NuGet package (`DictionarySlim<TKey,TValue>`).

Requires `clang` and `zlib1g-dev` (installed by `setup_dependencies.sh`).

---

## F#

Build system: `dotnet build` (JIT; no AOT)

All benchmarks share `build_common.sh` which generates a `.fsproj` and builds with:

- `PublishAot=false`, `ImplicitUsings=enable`, `Nullable=enable`, `AllowUnsafeBlocks=true`
- `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`
- Target framework: `net9.0`
- Output: shell wrapper (`#!/bin/sh exec dotnet "$DLL" "$@"`) — requires .NET runtime on `$PATH`; not a standalone native binary

| Benchmark      | Extra project settings                                                     |
|----------------|----------------------------------------------------------------------------|
| k-nucleotide   | Adds `Microsoft.Experimental.Collections` (1.0.6-e190117-3) NuGet package |
| all others     | No extra settings                                                          |

---

## Swift

Compiler: `swiftc`

Flags (all benchmarks): `-Ounchecked -wmo`

- `-Ounchecked`: maximum optimization, skips safety checks
- `-wmo`: whole-module optimization

Note: regex-redux uses `NSRegularExpression` (ICU engine via Foundation) instead of PCRE2 — a material algorithmic difference from C/C++/Rust implementations.

---

## Dart

Build system: `dart compile exe`

No extra flags. Compiles each `main.dart` to a self-contained native executable.

---

## Erlang

Compiler: `erlc`

No extra `erlc` command-line flags. Runtime invocation uses `erl -noshell -smp enable` on all benchmarks; regex-redux additionally passes `-noinput`.

Source-level `-compile()` directives present in some files:
- `fannkuchredux.erl`, `regexredux.erl`: `-compile([native, {hipe, [o3]}])` — no-op under OTP 26+ (HiPE removed); BeamAsm JIT takes effect instead
- `spectralnorm.erl`: `-compile([inline, {inline_size, 1000}])` — genuine compile-time inlining optimization, honoured by `erlc`

---

## PHP

Runtime: `php` (CLI)

No compilation step. A shell wrapper is generated at setup time by `build_in_tmp.sh` that invokes `php` with the correct flags.

Base flags (all benchmarks): `-dzend_extension=<opcache.so> -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n`

- `-dzend_extension=<opcache.so>`: loads OPcache (path resolved at setup time via `extension_dir`)
- `-dopcache.enable_cli=1`: enables OPcache for CLI scripts
- `-dopcache.jit_buffer_size=64M`: allocates JIT buffer and enables JIT compilation
- `-n`: ignore `php.ini`; all extensions must be loaded explicitly

| Benchmark      | Extra flags                                             | Notes                                              |
|----------------|---------------------------------------------------------|----------------------------------------------------|
| binary-trees   | `-d memory_limit=4096M`                                 | Also loads `shmop`, `pcntl` extensions             |
| fannkuch-redux |                                                         | Also loads `shmop`, `pcntl` extensions             |
| fasta          |                                                         |                                                    |
| k-nucleotide   | `-d memory_limit=1024M -d short_open_tag=1`             | Also loads `pcntl`, `sysvmsg` extensions           |
| mandelbrot     | `-d short_open_tag=1`                                   | Also loads `shmop`, `pcntl` extensions             |
| n-body         | `-d short_open_tag=1`                                   |                                                    |
| regex-redux    | `-d memory_limit=512M`                                  | Also loads `pcntl`, `sysvmsg` extensions           |
| spectral-norm  | `-d short_open_tag=1`                                   | Also loads `pcntl` extension                       |

---

## Ruby

Runtime: `ruby` (CLI)

No compilation step. A shell wrapper is generated at setup time by `build_in_tmp.sh` that invokes `ruby` with the correct flags.

Flags (all benchmarks): `--yjit -W0`

- `--yjit`: enables Ruby's YJIT JIT compiler
- `-W0`: suppresses all warnings

---

## Python

Runtime: `python3` (CLI)

No compilation step. Source files are executed directly in the GMT flow.

Flags (all benchmarks): `-OO`

- `-OO`: removes `assert` statements and strips docstrings from bytecode

| Benchmark    | Extra setup                                    |
|--------------|------------------------------------------------|
| regex-redux  | Installs `libpcre2-8-0` via `apt-get`; uses PCRE2 via `ctypes` (not Python `re` module) |
| all others   |                                                |

---

## Lua

Runtime: `lua` (PUC Lua 5.5, image `nickblah/lua:5.5-luarocks-alpine3.22`)

Build step: `luac` pre-compiles each `.lua` source to Lua bytecode (`.lua_run` file) in `build_in_tmp.sh` before the timed flow. No extra `luac` or `lua` runtime flags. The VM interprets bytecode at runtime — no JIT.

| Benchmark    | Extra setup                                                                       |
|--------------|-----------------------------------------------------------------------------------|
| regex-redux  | Installs `gcc musl-dev make pcre2-dev` + `luarocks install lrexlib-pcre2`; uses PCRE2 JIT via `rex_pcre2:jit_compile()` |
| all others   |                                                                                   |

---

## Perl

Runtime: `perl` (image: `perl:5.42.1-threaded`)

No compilation step. Source is invoked directly in the GMT flow. No runtime flags.

The **threaded** Perl image variant is required: 6 of 8 benchmarks use Perl ithreads (`use threads`). Fasta and n-body are single-threaded.

| Benchmark      | Concurrency                                                                  |
|----------------|------------------------------------------------------------------------------|
| binary-trees   | `use threads`; `cpu_count` threads from `/proc/cpuinfo`; CPU-scaled          |
| fannkuch-redux | `use threads`; **12 fixed threads** (= input N=12); does not scale with CPU  |
| fasta          | Single-threaded                                                               |
| k-nucleotide   | `use threads`; `cpu_count` threads per frame; CPU-scaled                     |
| mandelbrot     | `use threads`; `cpu_count` threads; CPU-scaled                               |
| n-body         | Single-threaded                                                               |
| regex-redux    | Hybrid: `fork` + 3 fixed ithreads in child process                           |
| spectral-norm  | `use threads`; `cpu_count` threads; CPU-scaled                               |

---

## NodeJS

Runtime: `node` (V8/TurboFan JIT, image `node:25-alpine3.21`)

No compilation step. Source files are executed directly in the GMT flow. No runtime flags.

All benchmarks use `worker_threads` for parallelism except n-body (single-threaded).

| Benchmark      | Worker count                                                  |
|----------------|---------------------------------------------------------------|
| binary-trees   | One worker per depth-level task (task-count-derived)          |
| fannkuch-redux | `os.cpus().length` (CPU-scaled)                               |
| fasta          | **4 hardcoded** (`const cpus = 4`)                            |
| k-nucleotide   | **4 hardcoded**                                               |
| mandelbrot     | `os.cpus().length` (CPU-scaled)                               |
| n-body         | Single-threaded (no `worker_threads`)                         |
| regex-redux    | **1 worker** (main thread + 1 background replace task)        |
| spectral-norm  | `os.cpus().length` (CPU-scaled)                               |
