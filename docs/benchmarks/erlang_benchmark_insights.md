# Erlang Benchmark Insights

**Language:** Erlang  
**OTP version:** 29.0.0  
**Docker image:** `erlang:29.0.0` (all benchmarks)  
**Execution model:** `erlc` compiles `.erl` source to BEAM bytecode (`.beam` files). The BEAM VM in OTP 24+ includes BeamAsm, a JIT compiler that compiles BEAM bytecode to native machine code at load time. OTP 29.0.0 is well beyond the OTP 24 threshold, so **BeamAsm JIT is active** for all benchmarks. No explicit flags disable JIT; it is on by default.

---

## Per-Benchmark Breakdown

> **Binary-Trees — Erlang**
> - Execution: BEAM bytecode via `erlc` (no extra compile flags), run on BEAM VM with BeamAsm JIT (OTP 29.0.0)
> - Concurrency: **Multi-process.** Uses `rpc:pmap/3` at `binarytrees.erl:31` to farm out per-depth iterations in parallel. Each depth level `D` (stepping by 2 from `Min` to `Max`) is computed in a separate Erlang process spawned by `rpc:pmap`. Number of processes equals the number of depth levels in the range, not pinned to CPU count; BEAM SMP schedulers dispatch them across available cores.
> - Build/runtime config: Compile — `erlc /tmp/repo/benchmarks/erlang/binary-trees/binarytrees.erl` (no extra flags). Runtime — `erl -pa /tmp/repo/benchmarks/erlang/binary-trees -noshell -smp enable -run binarytrees main 21`
> - Source of flags: `binary-trees.yml:9` (compile), `binary-trees.yml:17` (runtime)

---

> **Fannkuch-Redux — Erlang**
> - Execution: BEAM bytecode via `erlc`, run on BEAM VM with BeamAsm JIT (OTP 29.0.0). Source also carries `-compile([native, {hipe, [o3]}])` at `fannkuchredux.erl:8`, which requests HiPE native compilation with O3. In OTP 24+ with BeamAsm, the `native` directive is treated as a no-op (HiPE was deprecated in OTP 24 and removed in OTP 26); the BeamAsm JIT handles native compilation instead.
> - Concurrency: **Multi-process.** `divide/4` at `fannkuchredux.erl:33` calls `spawn(Fun)` once per permutation chunk (N chunks for input N), then `join/3` at `fannkuchredux.erl:36–40` collects results via `receive`. Each chunk processes a contiguous range of permutation indices concurrently. For N=12, 12 worker processes are spawned; BEAM SMP schedulers distribute them across available cores.
> - Build/runtime config: Compile — `erlc /tmp/repo/benchmarks/erlang/fannkuch-redux/fannkuchredux.erl` (no extra flags; `-compile([native, {hipe, [o3]}])` is a source-level directive, a no-op under OTP 26+). Runtime — `erl -pa /tmp/repo/benchmarks/erlang/fannkuch-redux -noshell -smp enable -run fannkuchredux main 12`
> - Source of flags: `fannkuch-redux.yml:9` (compile), `fannkuch-redux.yml:17` (runtime), `fannkuchredux.erl:8` (source directive)

---

> **Fasta — Erlang**
> - Execution: BEAM bytecode via `erlc` (no extra compile flags), run on BEAM VM with BeamAsm JIT (OTP 29.0.0)
> - Concurrency: **Single-process.** No `spawn` call anywhere in `fasta.erl`. All work (ALU cycling, random nucleotide generation, output) is done sequentially in a single Erlang process. Uses a port (`open_port({fd,0,1}, ...)` at `fasta.erl:22`) for efficient binary I/O, but this is not a separate computation process.
> - Build/runtime config: Compile — `erlc /tmp/repo/benchmarks/erlang/fasta/fasta.erl` (no extra flags). Runtime — `erl -pa /tmp/repo/benchmarks/erlang/fasta -noshell -smp enable -run fasta main 25000000`. `-smp enable` is present but has no concurrency benefit here since the workload is single-process.
> - Source of flags: `fasta.yml:9` (compile), `fasta.yml:17` (runtime)

---

> **K-Nucleotide — Erlang**
> - Execution: BEAM bytecode via `erlc` (no extra compile flags), run on BEAM VM with BeamAsm JIT (OTP 29.0.0)
> - Concurrency: **Multi-process.** `do/2` at `knucleotide.erl:63` calls `spawn/1` to create one worker process per Action entry. Seven actions are defined at `knucleotide.erl:81–87`; therefore 7 worker processes are spawned concurrently. Workers use ETS hash tables and communicate results via message passing using a token-passing chain (`hd(Pids) ! tl(Pids) ++ [self()]` at `knucleotide.erl:91`) to enforce ordered printing. BEAM SMP schedulers run the workers across available cores.
> - Build/runtime config: Compile — `erlc /tmp/repo/benchmarks/erlang/k-nucleotide/knucleotide.erl` (no extra flags). Runtime — `erl -pa /tmp/repo/benchmarks/erlang/k-nucleotide -noshell -smp enable -run knucleotide main dummy < /tmp/repo/inputs/fasta-2500000.txt` (stdin redirect requires `shell: sh`)
> - Source of flags: `k-nucleotide.yml:9` (compile), `k-nucleotide.yml:18` (runtime)

---

> **Mandelbrot — Erlang**
> - Execution: BEAM bytecode via `erlc` (no extra compile flags), run on BEAM VM with BeamAsm JIT (OTP 29.0.0)
> - Concurrency: **Multi-process.** `spawn_proc_chain/3` at `mandelbrot.erl:29–30` spawns one Erlang process per image row (N processes for an N×N image; N=16000). Each row process computes its pixels independently. A separate `print_start()` spawned process (`mandelbrot.erl:88`) handles serialized output via message passing. Row ordering is preserved by passing a `done` token down the chain. BEAM SMP schedulers distribute the row processes across available cores; at N=16000, 16001 processes are in flight.
> - Build/runtime config: Compile — `erlc /tmp/repo/benchmarks/erlang/mandelbrot/mandelbrot.erl` (no extra flags). Runtime — `erl -pa /tmp/repo/benchmarks/erlang/mandelbrot -noshell -smp enable -run mandelbrot main 16000`
> - Source of flags: `mandelbrot.yml:9` (compile), `mandelbrot.yml:17` (runtime)

---

> **N-Body — Erlang**
> - Execution: BEAM bytecode via `erlc` (no extra compile flags), run on BEAM VM with BeamAsm JIT (OTP 29.0.0)
> - Concurrency: **Single-process.** No `spawn` call in `nbody.erl`. The simulation loop (`advance/3` at `nbody.erl:52–53`) iterates 50,000,000 steps sequentially in a single process using purely functional list operations and floating-point arithmetic with guard-enforced float specialization (`?f(X)` macros at `nbody.erl:13`). `-smp enable` is present but has no concurrency benefit here.
> - Build/runtime config: Compile — `erlc /tmp/repo/benchmarks/erlang/n-body/nbody.erl` (no extra flags). Runtime — `erl -pa /tmp/repo/benchmarks/erlang/n-body -noshell -smp enable -run nbody main 50000000`
> - Source of flags: `n-body.yml:9` (compile), `n-body.yml:17` (runtime)

---

> **Regex-Redux — Erlang**
> - Execution: BEAM bytecode via `erlc` (no extra compile flags), run on BEAM VM with BeamAsm JIT (OTP 29.0.0). Source carries `-compile([native, {hipe, [o3]}])` at `regexredux.erl:22`, which is a no-op under OTP 26+ (HiPE removed); BeamAsm JIT handles native compilation instead.
> - Concurrency: **Multi-process.** `work/1` at `regexredux.erl:36` spawns one `spawn_link` worker process per regex pattern via `matcher/4` closures (`regexredux.erl:45–47`). Nine patterns are defined at `regexredux.erl:80–87`, so 9 matcher processes run concurrently plus an initial `Worker = spawn_link(fun () -> work(S) end)` at `regexredux.erl:32`. BEAM SMP schedulers dispatch matchers across available cores. Results are collected in order via `results/1` at `regexredux.erl:75–77`. A `spawn_link` is used rather than `spawn`, so crashes propagate to the supervisor.
> - Build/runtime config: Compile — `erlc /tmp/repo/benchmarks/erlang/regex-redux/regexredux.erl` (no extra flags). Runtime — `erl -pa /tmp/repo/benchmarks/erlang/regex-redux -noshell -noinput -smp enable -run regexredux main 0 < /tmp/repo/inputs/fasta-5000000.txt`. Note `-noinput` is present here (in addition to `-noshell`) — this is the only benchmark with both flags.
> - Source of flags: `regex-redux.yml:9` (compile), `regex-redux.yml:18` (runtime), `regexredux.erl:22` (source directive)

---

> **Spectral-Norm — Erlang**
> - Execution: BEAM bytecode via `erlc` (no extra compile flags), run on BEAM VM with BeamAsm JIT (OTP 29.0.0). Source carries `-compile([inline, {inline_size, 1000}])` at `spectralnorm.erl:7`, which instructs the Erlang compiler to aggressively inline functions up to size 1000. This is a compile-time optimization that is honoured by `erlc`.
> - Concurrency: **Multi-process, scales with logical CPU count.** `pmap/2` at `spectralnorm.erl:58–62` calls `erlang:system_info(logical_processors)` to determine the number of chunks, then spawns one Erlang process per chunk via `spawn/1`. Each process computes a slice of the matrix-vector product and sends results back via message passing. Chunk count (and thus worker process count) is dynamically set equal to the number of logical processors reported by the BEAM VM — this is the only benchmark that explicitly queries and adapts to hardware parallelism. BEAM SMP schedulers run the workers across all cores.
> - Build/runtime config: Compile — `erlc /tmp/repo/benchmarks/erlang/spectral-norm/spectralnorm.erl` (no extra flags; `-compile([inline, {inline_size, 1000}])` is a source directive honoured by `erlc`). Runtime — `erl -pa /tmp/repo/benchmarks/erlang/spectral-norm -noshell -smp enable -run spectralnorm main 5500`
> - Source of flags: `spectral-norm.yml:9` (compile), `spectral-norm.yml:17` (runtime), `spectralnorm.erl:7` (inline directive)

---

## Discrepancy log

1. **`flags.md` states "no extra compiler flags"** — this is broadly accurate for `erlc` invocations (all YAMLs pass only the source file path, no `-W`, `-O`, or other `erlc` flags). However, three source files contain `-compile(...)` module attributes that function as compile-time directives:
   - `fannkuchredux.erl:8`: `-compile([native, {hipe, [o3]}])` — requests HiPE native compilation. Under OTP 26+, HiPE was removed and this directive is silently ignored; BeamAsm JIT takes effect instead. `flags.md` does not mention this.
   - `regexredux.erl:22`: `-compile([native, {hipe, [o3]}])` — same situation as above.
   - `spectralnorm.erl:7`: `-compile([inline, {inline_size, 1000}])` — aggressive inlining is a genuine compile-time optimization that `erlc` does apply. `flags.md` does not mention this.

2. **`flags.md` does not mention `-noshell`** (present in all benchmarks) or **`-noinput`** (present only in regex-redux at `regex-redux.yml:18`). These are standard runtime flags for non-interactive invocations and do not affect performance, but they are part of the actual runtime configuration.

3. **`flags.md` does not specify a scheduler count** (`+S` flag). No benchmark passes `+S`; the BEAM VM defaults to using all available logical processors as SMP schedulers. The spectral-norm source explicitly queries `erlang:system_info(logical_processors)` to match work partitioning to this default.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| Erlang | `erlc` → BEAM bytecode → BeamAsm JIT (OTP 29.0.0) | `-smp enable` (runtime, all benchmarks); no extra `erlc` flags | Multi-process via `spawn`/`rpc:pmap`/`spawn_link` (binary-trees, fannkuch-redux, k-nucleotide, mandelbrot, regex-redux, spectral-norm); single-process (fasta, n-body) | BeamAsm JIT active (OTP ≥ 24). `fannkuchredux.erl` and `regexredux.erl` carry `-compile([native, {hipe, [o3]}])` — no-op under OTP 29 (HiPE removed in OTP 26). `spectralnorm.erl` uses `-compile([inline, {inline_size, 1000}])` for aggressive inlining — this is honoured by `erlc`. Spectral-norm uniquely queries `erlang:system_info(logical_processors)` to partition work to CPU count. Regex-redux is the only benchmark with both `-noshell` and `-noinput` runtime flags. No benchmark passes `+S` — BEAM defaults to all logical processors as SMP schedulers. |
