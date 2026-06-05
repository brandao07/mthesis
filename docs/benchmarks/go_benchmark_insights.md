# Go Benchmark Insights

**Language:** Go  
**Go version:** 1.25  
**Docker image:** `golang:1.25-alpine` (all 8 benchmarks)

All benchmarks are AOT-compiled inside the container via `go build` with no extra build flags. No `build_in_tmp.sh` script exists for any Go benchmark. Regex-redux is the only outlier in build procedure (module init + external dependency); all others compile a single `main.go` directly.

---

## binary-trees — Go

- **Execution:** AOT via `go build` (Go 1.25), no extra flags. Command: `go build -o /tmp/go-binary-trees /tmp/repo/benchmarks/go/binary-trees/main.go`. Run: `/tmp/go-binary-trees 21`.
  - Source: `binary-trees.yml:9`, `binary-trees.yml:17`
- **Concurrency:** Multi-goroutine. `sync.WaitGroup` is used to launch one goroutine for the stretch tree, one for the long-lived tree, and one goroutine per depth level (up to `(maxDepth-minDepth)/2 + 1` depth bands) — all concurrent. Goroutines share no mutable state except the pre-allocated `outBuff` slice (each writes to a distinct index). No explicit `GOMAXPROCS` call; defaults to the number of logical CPUs available in the container (runtime default since Go 1.5). Parallelism scales naturally with CPU count via the Go runtime scheduler.
  - Source: `binary-trees/main.go:72–133`
- **Build/runtime config:** No build flags. `GOMAXPROCS` not set explicitly — Go runtime default (= number of available logical CPUs).
- **Source of flags:** `binary-trees.yml:9`
- **Notes:** Allocates and traverses many short-lived heap objects; Go's concurrent, tri-color mark-sweep GC is under heavy pressure here. GC pause and throughput behavior is a material factor for energy and wall-clock performance on this benchmark.

---

## fannkuch-redux — Go

- **Execution:** AOT via `go build` (Go 1.25), no extra flags. Command: `go build -o /tmp/go-fannkuch-redux /tmp/repo/benchmarks/go/fannkuch-redux/main.go`. Run: `/tmp/go-fannkuch-redux 12`.
  - Source: `fannkuch-redux.yml:9`, `fannkuch-redux.yml:17`
- **Concurrency:** Multi-goroutine with **hardcoded `GOMAXPROCS(4)`**. The `fannkuch` function spawns a new goroutine for each chunk of the permutation space (up to `NTASKS = (Fact[n] + CHUNKSZ - 1) / CHUNKSZ` tasks, where `NCHUNKS = 720`). Goroutines communicate only via a `chan bool` result channel and `sync/atomic` operations on shared `res` and `chk` accumulators. Work is chunked at compile-time-constant granularity. Parallelism is pinned to exactly 4 OS threads regardless of actual CPU count.
  - Source: `fannkuch-redux/main.go:149`, `fannkuch-redux/main.go:40–44`, `fannkuch-redux/main.go:128–134`
- **Build/runtime config:** No build flags. `runtime.GOMAXPROCS(4)` hardcoded in `main()`.
- **Source of flags:** `fannkuch-redux/main.go:149`
- **Notes:** Unlike most other Go benchmarks, parallelism does NOT scale with CPU count — it is fixed at 4 threads. This is a deliberate CLBG implementation choice and may underutilize cores on machines with > 4 logical CPUs.

---

## fasta — Go

- **Execution:** AOT via `go build` (Go 1.25), no extra flags. Command: `go build -o /tmp/go-fasta /tmp/repo/benchmarks/go/fasta/main.go`. Run: `/tmp/go-fasta 25000000`.
  - Source: `fasta.yml:9`, `fasta.yml:17`
- **Concurrency:** Multi-goroutine. `runtime.GOMAXPROCS(runtime.NumCPU())` is set explicitly to the number of logical CPUs. In `RandomFasta`, goroutines are spawned in a pipeline pattern: a queue of `chan []byte` futures (`och`) decouples DNA generation from output. One writer goroutine drains `och` in order; one generator goroutine per chunk handles the DNA lookup. `RepeatFasta` is fully sequential. Parallelism scales with CPU count (for the random-fasta sections).
  - Source: `fasta/main.go:159`, `fasta/main.go:130–155`
- **Build/runtime config:** No build flags. `runtime.GOMAXPROCS(runtime.NumCPU())` set at program start.
- **Source of flags:** `fasta/main.go:159`
- **Notes:** Pipelined goroutine model overlaps compute (DNA lookup) and I/O (buffered stdout write). The LCG random number generator (`generateRandom`) is sequential and is a bottleneck since it maintains global state (`lastrandom`).

---

## k-nucleotide — Go

- **Execution:** AOT via `go build` (Go 1.25), no extra flags. Command: `go build -o /tmp/go-k-nucleotide /tmp/repo/benchmarks/go/k-nucleotide/main.go`. Run: `/tmp/go-k-nucleotide < /tmp/repo/inputs/fasta-25000000.txt` (stdin redirect).
  - Source: `k-nucleotide.yml:9`, `k-nucleotide.yml:17–18`
- **Concurrency:** Multi-goroutine scaling with CPU count. `startCount32` and `startCount64` each spawn exactly `runtime.NumCPU()` goroutines, one per logical CPU, coordinated via `sync.WaitGroup`. Each goroutine processes a strided partition of the data (offset `begin`, stride `goroutineCount`), building an independent local map; results are merged serially after `wg.Wait()`. `runtime.GOMAXPROCS` is not set explicitly — defaults to `runtime.NumCPU()` (Go runtime default).
  - Source: `k-nucleotide/main.go:144–172`, `k-nucleotide/main.go:204–253`
- **Build/runtime config:** No build flags. `GOMAXPROCS` not set — Go runtime default (= logical CPU count).
- **Source of flags:** `k-nucleotide.yml:9`
- **Notes:** Each query (WriteFrequencies, WriteCount) is processed sequentially, but the counting within each query is parallelised over all CPUs. No shared mutable state between goroutines during counting (separate maps per goroutine; pointer-based map values avoid false sharing).

---

## mandelbrot — Go

- **Execution:** AOT via `go build` (Go 1.25), no extra flags. Command: `go build -o /tmp/go-mandelbrot /tmp/repo/benchmarks/go/mandelbrot/main.go`. Run: `/tmp/go-mandelbrot 16000`.
  - Source: `mandelbrot.yml:9`, `mandelbrot.yml:17`
- **Concurrency:** Multi-goroutine with **`GOMAXPROCS` set to `runtime.NumCPU() * 2`** (i.e., twice the logical CPU count). Exactly `pool = runtime.NumCPU() * 2` goroutines are launched via `go renderRows(wg, int32(size))`; they compete for rows using an `atomic.AddInt32` counter (`yAt`), implementing a work-stealing pattern. Results are written to a pre-allocated `rows` slice (each goroutine writes to a distinct index). `sync.WaitGroup` is used for barrier synchronisation.
  - Source: `mandelbrot/main.go:113–116`, `mandelbrot/main.go:140–146`
- **Build/runtime config:** No build flags. `runtime.GOMAXPROCS(runtime.NumCPU() * 2)` set in `main()`.
- **Source of flags:** `mandelbrot/main.go:113–115`
- **Notes:** The 2× oversubscription (goroutines > logical CPUs) is a deliberate CLBG pattern to keep hardware threads busy across the work-stealing row loop. Renders two pixels per inner loop iteration (dual unrolling with `Zr1`/`Zr2`). Output is the full PBM binary bitmap — I/O is a small fraction of total work at size 16000.

---

## n-body — Go

- **Execution:** AOT via `go build` (Go 1.25), no extra flags. Command: `go build -o /tmp/go-n-body /tmp/repo/benchmarks/go/n-body/main.go`. Run: `/tmp/go-n-body 50000000`.
  - Source: `n-body.yml:9`, `n-body.yml:17`
- **Concurrency:** **Single-threaded / sequential.** No goroutines, no channels, no `sync` package, no `GOMAXPROCS` call. All computation (`offsetMomentum`, `advance`, `energy`) runs on one goroutine in the main thread. The 50 million-step simulation is purely serial.
  - Source: `n-body/main.go` (full file — no `go` keyword usage, no `runtime` import)
- **Build/runtime config:** No build flags. No parallelism configuration.
- **Source of flags:** `n-body.yml:9`
- **Notes:** This is the only Go benchmark that is entirely single-threaded. Performance is governed purely by floating-point throughput and the Go compiler's scalar optimisation quality. Unlike the Rust n-body (which uses SIMD intrinsics), this implementation relies on the standard Go compiler's auto-vectorisation (limited in Go 1.25 compared to LLVM-based toolchains).

---

## regex-redux — Go

- **Execution:** AOT via `go build` (Go 1.25), no extra build flags beyond module setup. Build is more complex: `apk add gcc musl-dev pcre-dev` → `go mod init regex-redux` → `go get github.com/GRbit/go-pcre@v1.0.0` → `go build -o /tmp/go-regex-redux .` (builds module directory, not a single file). Run: `/tmp/go-regex-redux < /tmp/repo/inputs/fasta-25000000.txt` (stdin redirect).
  - Source: `regex-redux.yml:10–12`, `regex-redux.yml:20–21`
- **Concurrency:** Multi-goroutine with **`GOMAXPROCS` set to `runtime.NumCPU()`**. Nine match-counting goroutines are launched simultaneously (one per variant pattern), each writing its result to a dedicated `chan int`. One additional goroutine handles all five sequential substitutions and sends final length to `lenresult chan int`. Total: 10 concurrent goroutines plus main. Main goroutine collects results in order. Parallelism scales with CPU count (GOMAXPROCS = NumCPU).
  - Source: `regex-redux/main.go:61`, `regex-redux/main.go:77–95`
- **Build/runtime config:** No extra `go build` flags. Requires CGO (links against `libpcre`); `apk add gcc musl-dev pcre-dev` provides the C toolchain and PCRE library. External dependency: `github.com/GRbit/go-pcre@v1.0.0` (PCRE JIT bindings via CGO). `runtime.GOMAXPROCS(runtime.NumCPU())` set at startup.
- **Source of flags:** `regex-redux.yml:10–12`, `regex-redux/main.go:61`
- **Notes:** This is the only Go benchmark that uses CGO and an external library, and the only one whose build requires a Go module (vs. single-file `go build`). PCRE JIT compilation (`pcre.STUDY_JIT_COMPILE`) is used for all patterns, delegating regex execution to libpcre's native JIT rather than Go's `regexp` package (which uses a slower RE2 engine). This makes performance heavily dependent on the PCRE JIT's efficiency.

---

## spectral-norm — Go

- **Execution:** AOT via `go build` (Go 1.25), no extra flags. Command: `go build -o /tmp/go-spectral-norm /tmp/repo/benchmarks/go/spectral-norm/main.go`. Run: `/tmp/go-spectral-norm 5500`.
  - Source: `spectral-norm.yml:9`, `spectral-norm.yml:17`
- **Concurrency:** Multi-goroutine with **`GOMAXPROCS` set to `runtime.NumCPU() * 2`** (package-level `var NumCPU = runtime.NumCPU()*2`, applied via `runtime.GOMAXPROCS(NumCPU)` in `init()`). Both `mult_Av` and `mult_Atv` launch exactly `NumCPU` goroutines per call (each taking a contiguous slice partition), coordinated via `sync.WaitGroup`. The benchmark performs 10 iterations of `mult_AtAv`, so goroutines are spawned and joined 20 times per `SpectralNorm` call. Parallelism scales with CPU count (2× logical CPUs).
  - Source: `spectral-norm/main.go:19`, `spectral-norm/main.go:27–28`, `spectral-norm/main.go:69–91`, `spectral-norm/main.go:105–127`
- **Build/runtime config:** No build flags. `runtime.GOMAXPROCS(runtime.NumCPU() * 2)` applied in `init()`.
- **Source of flags:** `spectral-norm/main.go:19`, `spectral-norm/main.go:27`
- **Notes:** The 2× oversubscription matches the mandelbrot pattern. The inner loop (`A(i,j)`) involves integer arithmetic (`(i+j)*(i+j+1)/2 + i + 1`) — no SIMD. Unlike Rust spectral-norm (which uses SSE2 intrinsics), the Go version relies entirely on the compiler's scalar code generation.

---

## Discrepancy log

The `docs/flags.md` Go section states: "No extra flags. The Go toolchain's default release build is used for all benchmarks. Each benchmark compiles a single `main.go` file."

Two discrepancies were found:

1. **regex-redux build is not a single-file `go build`** — it initialises a Go module, fetches an external dependency (`github.com/GRbit/go-pcre@v1.0.0`), and builds the whole module directory. It also requires CGO and a native C library (`pcre-dev`). The flags.md description is inaccurate for this benchmark.
   - Evidence: `regex-redux.yml:10–12`

2. **`GOMAXPROCS` is set explicitly in several benchmarks** — flags.md implies all benchmarks use runtime defaults. In reality:
   - `fannkuch-redux`: hardcoded `GOMAXPROCS(4)` (`fannkuch-redux/main.go:149`)
   - `fasta`: `GOMAXPROCS(runtime.NumCPU())` (`fasta/main.go:159`)
   - `mandelbrot`: `GOMAXPROCS(runtime.NumCPU() * 2)` (`mandelbrot/main.go:114–115`)
   - `regex-redux`: `GOMAXPROCS(runtime.NumCPU())` (`regex-redux/main.go:61`)
   - `spectral-norm`: `GOMAXPROCS(runtime.NumCPU() * 2)` via `init()` (`spectral-norm/main.go:27–28`)
   - Only `binary-trees`, `k-nucleotide`, and `n-body` use the unmodified runtime default.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|---------------|-------------|-------|
| Go (binary-trees) | AOT (`go build`, Go 1.25) | None | Multi-goroutine; `GOMAXPROCS` = runtime default (NumCPU); goroutines scale with depth bands | Heavy GC pressure from short-lived tree nodes |
| Go (fannkuch-redux) | AOT (`go build`, Go 1.25) | None | Multi-goroutine; **`GOMAXPROCS` hardcoded to 4**; does NOT scale with CPU count | Unique among Go benchmarks: fixed parallelism |
| Go (fasta) | AOT (`go build`, Go 1.25) | None | Multi-goroutine pipeline; `GOMAXPROCS(runtime.NumCPU())`; scales with CPU count | LCG RNG is sequential bottleneck; pipelined output |
| Go (k-nucleotide) | AOT (`go build`, Go 1.25) | None | Multi-goroutine; `GOMAXPROCS` = runtime default (NumCPU); `runtime.NumCPU()` goroutines per query; scales with CPU count | Strided partition per goroutine; independent maps; serial merge |
| Go (mandelbrot) | AOT (`go build`, Go 1.25) | None | Multi-goroutine; `GOMAXPROCS(runtime.NumCPU() * 2)`; work-stealing via atomic counter; scales with CPU count (2×) | Dual-pixel unrolled inner loop; 2× oversubscription |
| Go (n-body) | AOT (`go build`, Go 1.25) | None | **Single-threaded**; no goroutines, no GOMAXPROCS | Only fully sequential Go benchmark; scalar FP only |
| Go (regex-redux) | AOT (`go build` + module + CGO, Go 1.25) | `github.com/GRbit/go-pcre@v1.0.0`; `libpcre` via CGO | Multi-goroutine; `GOMAXPROCS(runtime.NumCPU())`; 9+1 goroutines; scales with CPU count | Only CGO/external-dependency benchmark; PCRE JIT used |
| Go (spectral-norm) | AOT (`go build`, Go 1.25) | None | Multi-goroutine; `GOMAXPROCS(runtime.NumCPU() * 2)`; `NumCPU` goroutines per matrix-vector multiply; scales with CPU count (2×) | 2× oversubscription; 20 goroutine fan-out/join cycles per run |
