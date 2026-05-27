# Flags

Documents the compiler flags and build settings used for each language's benchmark YAMLs. Flags are derived from the CLBG reference implementations, adapted for the Docker environment (`-march=ivybridge` → `-march=native`; library installs via `apt-get`/`apk`/`opam` where needed).

---

## C

Compiler: `gcc`

| Benchmark      | Flags                                                                                    | Notes                                      |
|----------------|------------------------------------------------------------------------------------------|--------------------------------------------|
| binary-trees   | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp -I/usr/include/apr-1.0 -lapr-1` | Requires `libapr1-dev`                |
| fannkuch-redux | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -pthread`                            | Uses pthreads, not OpenMP                  |
| fasta          | `-pipe -Wall -O3 -fomit-frame-pointer -march=native`                                    |                                            |
| k-nucleotide   | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp`                           | `khash.h` is bundled in benchmark dir      |
| mandelbrot     | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -mno-fma -fno-finite-math-only -fopenmp` |                                       |
| n-body         | `-pipe -Wall -O3 -fomit-frame-pointer -march=native`                                    |                                            |
| regex-redux    | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp -lpcre2-8`                 | Requires `libpcre2-dev`                    |
| spectral-norm  | `-pipe -Wall -O3 -fomit-frame-pointer -march=native -fopenmp -lm`                       |                                            |

---

## C++

Compiler: `g++`

All benchmarks install `libboost-dev` in `setup-commands`.

| Benchmark      | Flags                                                                              | Notes                                        |
|----------------|------------------------------------------------------------------------------------|----------------------------------------------|
| binary-trees   | `-pipe -O3 -fomit-frame-pointer -march=native -std=gnu++17 -ltbb`                 | Requires `libtbb-dev libboost-dev` (uses `<execution>` and boost headers) |
| fannkuch-redux | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -fopenmp`                |                                              |
| fasta          | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -lpthread`               | Requires `libboost-dev` (uses boost range headers) |
| k-nucleotide   | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -lpthread`               |                                              |
| mandelbrot     | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -mno-fma -pthread`       | Uses `<thread>`, not OpenMP                  |
| n-body         | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17`                         |                                              |
| regex-redux    | `-pipe -O3 -fomit-frame-pointer -march=native -std=c++17 -lpcre2-8 -lpthread`     | Requires `libboost-dev` (uses boost headers) |
| spectral-norm  | `-pipe -O3 -fomit-frame-pointer -march=native -fopenmp`                            |                                              |

---

## Rust

Build system: `cargo` (most benchmarks) or direct `rustc` (n-body).

`RUSTFLAGS` are set in each benchmark's `build_in_tmp.sh`.

| Benchmark      | RUSTFLAGS / command                                                   | Notes                          |
|----------------|-----------------------------------------------------------------------|--------------------------------|
| binary-trees   | `-C opt-level=3 -C target-cpu=ivybridge -C codegen-units=1`         | Should be `native` — inconsistency to fix |
| fannkuch-redux | `-C opt-level=3 -C target-cpu=ivybridge -C codegen-units=1`         | Should be `native` — inconsistency to fix |
| fasta          | `-C opt-level=3 -C target-cpu=native -C codegen-units=1`            |                                |
| k-nucleotide   | `-C opt-level=3 -C target-cpu=native -C codegen-units=1`            |                                |
| mandelbrot     | `-C opt-level=3 -C target-cpu=native -C codegen-units=1`            |                                |
| n-body         | `rustc -C opt-level=3 -C target-cpu=native -C codegen-units=1`      | Direct rustc, no Cargo         |
| regex-redux    | `-C opt-level=3 -C target-cpu=native -C codegen-units=1`            |                                |
| spectral-norm  | `-C opt-level=3 -C target-cpu=native -C codegen-units=1`            |                                |

---

## Go

Build system: `go build`

No extra flags. The Go toolchain's default release build is used for all benchmarks. Each benchmark compiles a single `main.go` file.

---

## Java (GraalVM AOT)

Steps: `javac` → `native-image`

`native-image` base flags: `-O3 -march=native`. GC: `--gc=G1` (with fallback to `--gc=serial`) for all benchmarks **except binary-trees**, which uses no GC flag (matches CLBG).

| Benchmark      | Extra native-image flags                                                                                                                                                          | Extra notes                                                                                              |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| binary-trees   | _(none — no `--gc` flag per CLBG)_                                                                                                                                               |                                                                                                          |
| k-nucleotide   |                                                                                                                                                                                   | Requires `fastutil-8.3.1.jar` (downloaded at setup)                                                     |
| regex-redux    | `-H:+UnlockExperimentalVMOptions -H:+ForeignAPISupport --enable-native-access=ALL-UNNAMED --features=ForeignRegistrationFeature -Djava.library.path=Include/java/jextract_pcre2` | `build_in_tmp.sh` downloads jextract-22 (build 6-47), installs `libpcre2-dev`/`pcre2-devel`, generates `jextract_pcre2` bindings, then compiles |
| all others     |                                                                                                                                                                                   |                                                                                                          |

---

## Haskell

Compiler: `ghc`

Base flags for most benchmarks: `-O2 -XBangPatterns -threaded -rtsopts -XMagicHash`

Runtime flags: `+RTS -N4` (4 threads) on all benchmarks; some add heap/stack limits.

| Benchmark      | Extra compile flags                                                          | Extra runtime flags  | Notes                              |
|----------------|------------------------------------------------------------------------------|----------------------|------------------------------------|
| binary-trees   | (base)                                                                        | `-K128M -H`          | Requires `parallel`, `ghc-compact` |
| fannkuch-redux | (base)                                                                        |                      |                                    |
| fasta          | (base)                                                                        |                      | Requires `massiv`                  |
| k-nucleotide   | (base)                                                                        | `-K2048M`            | Requires `parallel`, `hashable`, `hashtables`, `containers`, `bytestring` |
| mandelbrot     | `-fllvm -XUnboxedTuples`                                                     |                      | Requires LLVM (`llvm-*`, `clang-*`) installed at setup |
| n-body         | (base)                                                                        |                      |                                    |
| regex-redux    | `-XForeignFunctionInterface -XCApiFFI -optc "-DPCRE2_CODE_UNIT_WIDTH=8" -lpcre2-8` | `-H250M`       | Requires `libpcre2-dev`, `vector`  |
| spectral-norm  | (base)                                                                        |                      |                                    |

---

## OCaml

Compiler: `ocamlopt` (via `opam exec`); regex-redux uses `ocamlfind ocamlopt`

Flags (all benchmarks): `-noassert -unsafe -nodynlink -inline 100 -O3 -ccopt -fPIC -ccopt -march=ivybridge`

> **Note:** `-march=ivybridge` should be `-march=native` — inconsistency to fix across all 8 benchmarks.

| Benchmark      | Extra flags / notes                                      |
|----------------|----------------------------------------------------------|
| binary-trees   | `-I +unix unix.cmxa`                                    |
| regex-redux    | Uses `ocamlfind`; links `re` or `re.pcre` package        |
| all others     | No extra flags beyond the base set                       |

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

All benchmarks use identical project settings — no per-benchmark overrides.

Requires `clang` and `zlib1g-dev` (installed by `setup_dependencies.sh`).

---

## F#

Build system: `dotnet build` (JIT; no AOT)

All benchmarks share `build_common.sh` which generates a `.fsproj` and builds with:

- `PublishAot=false`, `ImplicitUsings=enable`, `Nullable=enable`, `AllowUnsafeBlocks=true`
- `ServerGarbageCollection=true`, `ConcurrentGarbageCollection=true`
- Target framework: `net9.0`
- Output: native `program` binary (self-contained launcher, runs directly)

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

---

## Dart

Build system: `dart compile exe`

No extra flags. Compiles each `main.dart` to a self-contained native executable.

---

## Erlang

Compiler: `erlc`

No extra compiler flags. Runtime invocation uses `erl -smp enable` to enable SMP/parallelism.

---

## Interpreted Languages

No compilation step. The runtime is invoked directly in the GMT flow.

| Language | Runtime         |
|----------|-----------------|
| Lua      | `lua`           |
| Perl     | `perl`          |
| PHP      | `php`           |
| Python   | `python3`       |
| Ruby     | `ruby`          |
| NodeJS   | `node`          |
