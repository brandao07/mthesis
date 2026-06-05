# Lua Benchmark Insights

## Runtime: PUC Lua 5.5 — Interpreted Bytecode VM (NOT LuaJIT)

- **Image**: `nickblah/lua:5.5-luarocks-alpine3.22` (all 8 benchmarks)
- **Runtime**: Standard PUC-Rio Lua 5.5, invoked as `lua`
- **JIT**: None. This is the reference bytecode interpreter. LuaJIT is not present in this image.
- **Pre-compilation**: All benchmarks use `luac` in `build_in_tmp.sh` to compile `.lua` source to Lua bytecode (`.lua_run` file) before the timed measurement. The `lua` VM then executes the pre-compiled bytecode at runtime. This eliminates parse/compile overhead from the measured window but does not change the execution model — the VM still interprets bytecode at runtime, with no JIT.

---

## Per-Benchmark Breakdown

> **Binary-Trees — Lua**
> - Execution: Interpreted PUC Lua 5.5 bytecode VM via `lua`; source pre-compiled with `luac` to `/tmp/lua-build/binary-trees/binarytrees.lua-4.lua_run`
> - Concurrency: Multi-process via `io.popen`. The parent process spawns child processes using `io.popen(("%s %s %d %d %d %d %d"):format(arg[-1], arg[0], ...))` — re-executing the same script with extra arguments designating chunk boundaries. Each child does a subset of the tree work and writes a partial sum to stdout, which the parent reads and accumulates. No threads, no coroutines. Parallelism is OS-level process forking, not Lua concurrency primitives. Default child count: `4` (hardcoded in `main.lua:15`; overridable via arg[2]).
> - Build/runtime config: No runtime flags. `luac` pre-compilation only (no flags to `luac` beyond input/output).
> - Source of flags: `benchmarks/lua/binary-trees/build_in_tmp.sh:14` (`luac -o binarytrees.lua-4.lua_run binarytrees.lua-4.lua`); `benchmarks/lua/binary-trees.yml:17` (`lua /tmp/lua-build/binary-trees/binarytrees.lua-4.lua_run 21`)

> **Fannkuch-Redux — Lua**
> - Execution: Interpreted PUC Lua 5.5 bytecode VM via `lua`; source pre-compiled with `luac` to `/tmp/lua-build/fannkuch-redux/fannkuchredux.lua_run`
> - Concurrency: Single-threaded. Pure sequential computation — one `fannkuch(n)` call iterating all permutations in a single loop. No coroutines, no `io.popen`, no forks.
> - Build/runtime config: No runtime flags. `luac` pre-compilation only.
> - Source of flags: `benchmarks/lua/fannkuch-redux/build_in_tmp.sh:14` (`luac -o fannkuchredux.lua_run fannkuchredux.lua`); `benchmarks/lua/fannkuch-redux.yml:17` (`lua /tmp/lua-build/fannkuch-redux/fannkuchredux.lua_run 12`)

> **Fasta — Lua**
> - Execution: Interpreted PUC Lua 5.5 bytecode VM via `lua`; source pre-compiled with `luac` to `/tmp/lua-build/fasta/fasta.lua-2.lua_run`
> - Concurrency: Single-threaded. Three sequential calls — `make_repeat_fasta`, then two `make_random_fasta` — with no coroutines or subprocesses. Notable: `make_random_fasta` uses `load()` to dynamically generate and compile a Lua chunk at runtime (`main.lua:27–41`), but this is executed in the same single thread.
> - Build/runtime config: No runtime flags. `luac` pre-compilation only.
> - Source of flags: `benchmarks/lua/fasta/build_in_tmp.sh:14` (`luac -o fasta.lua-2.lua_run fasta.lua-2.lua`); `benchmarks/lua/fasta.yml:17` (`lua /tmp/lua-build/fasta/fasta.lua-2.lua_run 25000000`)

> **K-Nucleotide — Lua**
> - Execution: Interpreted PUC Lua 5.5 bytecode VM via `lua`; source pre-compiled with `luac` to `/tmp/lua-build/k-nucleotide/knucleotide.lua-2.lua_run`
> - Concurrency: Single-threaded. Reads the entire input sequence into memory, then performs sequential frequency counting and fragment counting passes. No coroutines, no subprocesses.
> - Build/runtime config: No runtime flags. `luac` pre-compilation only. Reads from stdin via shell redirect (`< /tmp/repo/inputs/fasta-25000000.txt`), requiring `shell: sh` in the flow.
> - Source of flags: `benchmarks/lua/k-nucleotide/build_in_tmp.sh:14` (`luac -o knucleotide.lua-2.lua_run knucleotide.lua-2.lua`); `benchmarks/lua/k-nucleotide.yml:18` (`lua /tmp/lua-build/k-nucleotide/knucleotide.lua-2.lua_run 0 < /tmp/repo/inputs/fasta-25000000.txt`)

> **Mandelbrot — Lua**
> - Execution: Interpreted PUC Lua 5.5 bytecode VM via `lua`; source pre-compiled with `luac` to `/tmp/lua-build/mandelbrot/mandelbrot.lua-6.lua_run`
> - Concurrency: Multi-process via `io.popen`. Same pattern as binary-trees: the parent spawns child processes with `io.popen(("%s %s %d %d %d %d"):format(arg[-1], arg[0], ...))`, each computing a horizontal band of rows, writing binary output to stdout. The parent collects and re-emits in order. Default child count: `6` (hardcoded in `main.lua:18`; overridable via arg[2]).
> - Build/runtime config: No runtime flags. `luac` pre-compilation only.
> - Source of flags: `benchmarks/lua/mandelbrot/build_in_tmp.sh:14` (`luac -o mandelbrot.lua-6.lua_run mandelbrot.lua-6.lua`); `benchmarks/lua/mandelbrot.yml:17` (`lua /tmp/lua-build/mandelbrot/mandelbrot.lua-6.lua_run 16000`)

> **N-Body — Lua**
> - Execution: Interpreted PUC Lua 5.5 bytecode VM via `lua`; source pre-compiled with `luac` to `/tmp/lua-build/n-body/nbody.lua-2.lua_run`
> - Concurrency: Single-threaded. Runs `N=50000000` steps of a 5-body Newtonian simulation in a sequential `advance()` loop. No coroutines, no subprocesses.
> - Build/runtime config: No runtime flags. `luac` pre-compilation only.
> - Source of flags: `benchmarks/lua/n-body/build_in_tmp.sh:14` (`luac -o nbody.lua-2.lua_run nbody.lua-2.lua`); `benchmarks/lua/n-body.yml:17` (`lua /tmp/lua-build/n-body/nbody.lua-2.lua_run 50000000`)

> **Regex-Redux — Lua**
> - Execution: Interpreted PUC Lua 5.5 bytecode VM via `lua`; source pre-compiled with `luac` to `/tmp/lua-build/regex-redux/regexredux.lua_run`
> - Concurrency: Single-threaded. Sequential regex counting and substitution passes using the `rex_pcre2` (lrexlib-PCRE2) Lua binding. Each regex is compiled with `:jit_compile()` (`main.lua:32, 49, 66`) — this calls PCRE2's JIT compilation for the regex engine itself (not the Lua VM), giving faster regex matching.
> - Build/runtime config: No `lua` runtime flags. Setup installs native dependencies: `apk add --no-cache gcc musl-dev make pcre2-dev` then `luarocks install lrexlib-pcre2` (`regex-redux.yml:10–11`). `luac` pre-compilation only. Reads from stdin via shell redirect, requiring `shell: sh`.
> - Source of flags: `benchmarks/lua/regex-redux.yml:10–11` (setup-commands); `benchmarks/lua/regex-redux/build_in_tmp.sh:1–19` (luac step); `benchmarks/lua/regex-redux.yml:20` (flow command)

> **Spectral-Norm — Lua**
> - Execution: Interpreted PUC Lua 5.5 bytecode VM via `lua`; source pre-compiled with `luac` to `/tmp/lua-build/spectral-norm/spectralnorm.lua-7.lua_run`
> - Concurrency: Single-threaded. 10 power-iteration steps of `AtAv()` over vectors of size `N=5500`, all sequential. No coroutines, no subprocesses.
> - Build/runtime config: No runtime flags. `luac` pre-compilation only.
> - Source of flags: `benchmarks/lua/spectral-norm/build_in_tmp.sh:14` (`luac -o spectralnorm.lua-7.lua_run spectralnorm.lua-7.lua`); `benchmarks/lua/spectral-norm.yml:17` (`lua /tmp/lua-build/spectral-norm/spectralnorm.lua-7.lua_run 5500`)

---

## Discrepancy log

**Discrepancy found — flags.md misclassifies the execution model.**

`docs/flags.md` (Interpreted Languages table, line 232) lists Lua under "No compilation step. The runtime is invoked directly in the GMT flow." This is inaccurate in two respects:

1. **There IS a build step**: every benchmark runs `luac` in `build_in_tmp.sh` to pre-compile the `.lua` source to Lua bytecode before the timed flow. While this does not change the runtime execution model (the `lua` VM still interprets bytecode), it is a distinct setup-commands step, not a direct source invocation.
2. **Runtime command accuracy**: The `lua` runtime identifier in flags.md is correct — it is indeed PUC Lua (not LuaJIT). The image `nickblah/lua:5.5-luarocks-alpine3.22` provides standard Lua 5.5; there is no LuaJIT anywhere in the image name or flow commands.

**No discrepancy between flags.md and actual runtime** with respect to JIT: flags.md says `lua`, files confirm `lua`. LuaJIT is not used.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| Lua (binary-trees) | `luac` bytecode pre-compile; PUC Lua 5.5 interpreted VM at runtime | None | Multi-process (`io.popen` spawns 4 child processes) | Process-level parallelism; each child re-executes the same script with chunk args |
| Lua (fannkuch-redux) | `luac` bytecode pre-compile; PUC Lua 5.5 interpreted VM at runtime | None | Single-threaded | Pure sequential permutation loop |
| Lua (fasta) | `luac` bytecode pre-compile; PUC Lua 5.5 interpreted VM at runtime | None | Single-threaded | Uses `load()` for runtime codegen; still single-threaded |
| Lua (k-nucleotide) | `luac` bytecode pre-compile; PUC Lua 5.5 interpreted VM at runtime | None | Single-threaded | Reads stdin; sequential freq counting |
| Lua (mandelbrot) | `luac` bytecode pre-compile; PUC Lua 5.5 interpreted VM at runtime | None | Multi-process (`io.popen` spawns 6 child processes) | Process-level parallelism; each child computes a row band |
| Lua (n-body) | `luac` bytecode pre-compile; PUC Lua 5.5 interpreted VM at runtime | None | Single-threaded | 50M step sequential simulation |
| Lua (regex-redux) | `luac` bytecode pre-compile; PUC Lua 5.5 interpreted VM at runtime | None (lrexlib-pcre2 via luarocks) | Single-threaded | PCRE2 JIT (regex engine only, not Lua VM); `rex_pcre2:jit_compile()` per pattern |
| Lua (spectral-norm) | `luac` bytecode pre-compile; PUC Lua 5.5 interpreted VM at runtime | None | Single-threaded | Sequential power iteration |
