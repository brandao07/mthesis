# OCaml Benchmark Insights

**Language:** OCaml
**OCaml version:** 5.4 (image tag `ocaml/opam:ubuntu-24.04-ocaml-5.4`; YAML description string `OCaml 5.4.0+dev0-2024-08-25`)
**Docker image:** `ocaml/opam:ubuntu-24.04-ocaml-5.4` (all 8 benchmarks)

---

## Per-Benchmark Breakdown

> **Binary-Trees — OCaml**
> - Execution: AOT native via `opam exec -- ocamlopt` (OCaml 5.4) with `-noassert -unsafe -fPIC -nodynlink -inline 100 -O3 -I +unix unix.cmxa -ccopt -march=native`
> - Concurrency: **Multi-process via Unix `fork`**. The `invoke` helper (`binary-trees/main.ml:44–63`) calls `Unix.fork()` for each depth-pair worker, communicating results back through a `Unix.pipe()` using `Marshal`. The main process fans out `((max_depth - min_depth) / 2 + 1)` child processes (up to 9 for depth 21, one per even depth level from 4 to 21). Each child exits after marshalling its result; the parent collects them with `Unix.waitpid`. The number of children is fixed by the problem input, not by CPU count.
> - Build/runtime config: compile flags from `binary-trees/build_in_tmp.sh:9–19`; linked against `unix.cmxa` (standard Unix library); binary written to `/tmp/ocaml-binary-trees`; intermediate `.cmi/.cmx/.o` files removed post-build.
> - Source of flags: `benchmarks/ocaml/binary-trees/build_in_tmp.sh:9–19`
>
> Note: GC tuning is commented out in source (`main.ml:24`; the `Gc.set` line is a comment). No SIMD. Fork-based parallelism avoids OCaml's GIL (applicable to pre-OCaml-5 Thread; OCaml 5 introduces Domains, but this benchmark uses `fork` not `Domain`).

---

> **Fannkuch-Redux — OCaml**
> - Execution: AOT native via `opam exec -- ocamlopt` (OCaml 5.4) with `-noassert -unsafe -fPIC -nodynlink -inline 100 -O3 -I +unix unix.cmxa -ccopt -march=native`
> - Concurrency: **Multi-process via `Unix.open_process_in`** (re-exec self). The main process (detected by `Sys.argv` length of 2) spawns 32 worker sub-processes (`workers = 32`, `main.ml:10`), each being a re-invocation of the same binary with additional `lo` and `hi` arguments (`main.ml:95`). Workers run their permutation chunk sequentially and write two binary integers to stdout. The parent collects all 32 results via `input_binary_int`. The 32-worker count is hardcoded and does not scale with CPU count.
> - Build/runtime config: compile flags from `fannkuch-redux/build_in_tmp.sh:9–19`; linked against `unix.cmxa`; binary at `/tmp/ocaml-fannkuch-redux`; invoked with argument `12` (`fannkuch-redux.yml:17`).
> - Source of flags: `benchmarks/ocaml/fannkuch-redux/build_in_tmp.sh:9–19`
>
> Note: `Unix.open_process_in` shells out via the system shell. No `Domain`, no `Thread`. No SIMD.

---

> **Fasta — OCaml**
> - Execution: AOT native via `opam exec -- ocamlopt` (OCaml 5.4) with `-noassert -unsafe -fPIC -nodynlink -inline 100 -O3 -I +unix unix.cmxa -ccopt -march=native`
> - Concurrency: **Single-threaded / single-process**. Source (`fasta/main.ml`) contains no `Unix.fork`, no `Thread`, no `Domain`. All output is generated sequentially in the main thread.
> - Build/runtime config: compile flags from `fasta/build_in_tmp.sh:9–19`; linked against `unix.cmxa` (used for `output_bytes` via the Unix module, though standard `stdout` I/O could suffice — library is linked but the primary I/O uses `output_bytes stdout`); binary at `/tmp/ocaml-fasta`; invoked with argument `25000000` (`fasta.yml:17`).
> - Source of flags: `benchmarks/ocaml/fasta/build_in_tmp.sh:9–19`
>
> Note: No SIMD. Pure sequential workload.

---

> **K-Nucleotide — OCaml**
> - Execution: AOT native via `opam exec -- ocamlopt` (OCaml 5.4) with `-noassert -unsafe -fPIC -nodynlink -inline 100 -O3 -I +unix unix.cmxa -ccopt -march=native`
> - Concurrency: **Multi-process via Unix `fork`**. The `invoke` helper (`k-nucleotide/main.ml:199–215`) uses `Unix.fork()` with a `Unix.pipe()` and `Marshal` for IPC, identical in structure to binary-trees. The `parallelize` function (`main.ml:217–219`) maps `invoke` over 7 tasks (2 frequency counts + 5 specific sequence counts, `main.ml:222–233`), launching up to 7 child processes in parallel. Each child exits after writing its result; the parent collects in order. Task count (7) is fixed, not CPU-scaled.
> - Build/runtime config: compile flags from `k-nucleotide/build_in_tmp.sh:9–19`; reads from stdin (`fasta-25000000.txt` piped in, `k-nucleotide.yml:18`); linked against `unix.cmxa`; binary at `/tmp/ocaml-k-nucleotide`.
> - Source of flags: `benchmarks/ocaml/k-nucleotide/build_in_tmp.sh:9–19`
>
> Note: Uses custom hashtables (`Hashtbl.Make`) with bit-packed integer keys for performance. No SIMD.

---

> **Mandelbrot — OCaml**
> - Execution: AOT native via `opam exec -- ocamlopt` (OCaml 5.4) with `-noassert -unsafe -fPIC -nodynlink -inline 100 -O3 -I +unix unix.cmxa -ccopt -march=native`
> - Concurrency: **Multi-process via Unix `fork`** — 64 workers (`workers = 64`, `mandelbrot/main.ml:18`). The recursive `spawn` function (`main.ml:67–82`) forks 64 child processes in a chain: each fork creates a child that recurses to spawn the next, while the parent computes one row-band (`worker` function), waits for its child's exit, prints its own buffer, then exits. This creates a pipeline of 64 processes each responsible for `w / 64` rows (plus remainder distribution). Worker count is hardcoded at 64, not CPU-scaled.
> - Build/runtime config: compile flags from `mandelbrot/build_in_tmp.sh:9–19`; linked against `unix.cmxa`; binary at `/tmp/ocaml-mandelbrot`; invoked with argument `16000` (`mandelbrot.yml:17`).
> - Source of flags: `benchmarks/ocaml/mandelbrot/build_in_tmp.sh:9–19`
>
> Note: Output is a PBM binary bitmap (`P4` format). No SIMD intrinsics; bit-packing done manually. Byte assembly uses integer shifts and `Char.chr`.

---

> **N-Body — OCaml**
> - Execution: AOT native via `opam exec -- ocamlopt` (OCaml 5.4) with `-noassert -unsafe -fPIC -nodynlink -inline 100 -O3 -ccopt -march=native`
> - Concurrency: **Single-threaded / single-process**. Source (`n-body/main.ml`) contains no `Unix.fork`, no `Thread`, no `Domain`. Pure sequential simulation over 5 bodies for 50,000,000 steps.
> - Build/runtime config: compile flags from `n-body/build_in_tmp.sh:9–18`; notably **does NOT link `-I +unix unix.cmxa`** (no Unix library needed); binary at `/tmp/ocaml-n-body`; invoked with argument `50000000` (`n-body.yml:17`).
> - Source of flags: `benchmarks/ocaml/n-body/build_in_tmp.sh:9–18`
>
> Note: Absence of `unix.cmxa` is consistent with docs/flags.md (`n-body` row: "no `-I +unix unix.cmxa`"). No SIMD. Floating-point intensive: `sqrt`, multiply-accumulate in tight loops.

---

> **Regex-Redux — OCaml**
> - Execution: AOT native via `opam exec -- ocamlfind ocamlopt` (OCaml 5.4) with `-noassert -unsafe -fPIC -nodynlink -inline 100 -O3 -package <re|re.pcre> -package unix -linkpkg -ccopt -march=native`
> - Concurrency: **Two processes via Unix `fork`** (`regex-redux/main.ml:50`). A single `Unix.fork()` splits execution: the child process iterates over 9 variant patterns counting matches (`main.ml:51–52`), while the parent process performs 5 substitution passes (`main.ml:54–58`). The parent then calls `Unix.wait()` (`main.ml:59`) and prints the final lengths. Fixed 2-process split (parent + 1 child), not CPU-scaled.
> - Build/runtime config: uses `ocamlfind ocamlopt` instead of bare `ocamlopt` to resolve the `re` package; `re` package installed at container startup via `opam install -y ocamlfind re` (`regex-redux.yml:10`); build script probes for `re.pcre` first and falls back to `re` (`regex-redux/build_in_tmp.sh:14–17`); both `re`/`re.pcre` and `unix` linked via `-linkpkg`; reads from stdin (`fasta-25000000.txt`, `regex-redux.yml:20`); binary at `/tmp/ocaml-regex-redux`.
> - Source of flags: `benchmarks/ocaml/regex-redux/build_in_tmp.sh:19–31`
>
> Note: Unlike all other benchmarks, uses `ocamlfind` (package manager integration) and does NOT use `-I +unix unix.cmxa` directly — unix is resolved through `ocamlfind -package unix -linkpkg`. The `re` library is a pure-OCaml regex engine with PCRE syntax support (not the C PCRE2 library used by C/Rust benchmarks).

---

> **Spectral-Norm — OCaml**
> - Execution: AOT native via `opam exec -- ocamlopt` (OCaml 5.4) with `-noassert -unsafe -fPIC -nodynlink -inline 100 -O3 -I +unix unix.cmxa -ccopt -march=native`
> - Concurrency: **Single-threaded / single-process**. Source (`spectral-norm/main.ml`) contains no `Unix.fork`, no `Thread`, no `Domain`. Pure sequential power-iteration over two matrix-vector products.
> - Build/runtime config: compile flags from `spectral-norm/build_in_tmp.sh:9–19`; linked against `unix.cmxa`; binary at `/tmp/ocaml-spectral-norm`; invoked with argument `5500` (`spectral-norm.yml:17`).
> - Source of flags: `benchmarks/ocaml/spectral-norm/build_in_tmp.sh:9–19`
>
> Note: No SIMD. Floating-point intensive: `eval_A` involves integer arithmetic and float division; `eval_AtA_times_u` runs 10 paired matrix-vector multiply passes.

---

## Discrepancy Log

1. **Fasta — `unix.cmxa` linkage**: `docs/flags.md` (line 115) says fasta links `-I +unix unix.cmxa`. The build script confirms this (`fasta/build_in_tmp.sh:16`). However, the fasta source (`fasta/main.ml`) does not explicitly call any `Unix.*` function — it uses `output_bytes stdout` (stdlib `Stdlib` function), `output stdout`, and `print_char`/`print_string`. The `unix.cmxa` library is linked but not actively used in the source. This is a minor over-linking with no correctness impact; it matches the docs and the CLBG reference pattern.

2. **Spectral-norm — `unix.cmxa` linkage**: Same situation as fasta — `unix.cmxa` is linked (`spectral-norm/build_in_tmp.sh:16`) but the source (`spectral-norm/main.ml`) uses no Unix functions. Consistent with docs.

3. **Regex-redux — `re` vs `re.pcre` selection**: `docs/flags.md` (line 120) states "links `re` or `re.pcre`". This is accurately reflected: the build script probes for `re.pcre` first and falls back to `re` (`regex-redux/build_in_tmp.sh:14–17`). Both are OCaml pure-OCaml implementations of a PCRE-syntax engine, not a binding to the C PCRE2 library.

No other discrepancies found between `docs/flags.md` and the actual build scripts or YAML files.

---

## Summary Table Row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| OCaml (binary-trees) | AOT native (`ocamlopt`) | `-noassert -unsafe -fPIC -nodynlink -inline 100 -O3 -ccopt -march=native` | Multi-process, Unix `fork` (up to 9 children, fixed by depth) | Results piped via `Marshal` over `Unix.pipe` |
| OCaml (fannkuch-redux) | AOT native (`ocamlopt`) | same base flags | Multi-process, 32 workers via `Unix.open_process_in` (self re-exec), count hardcoded | Workers write binary ints to stdout |
| OCaml (fasta) | AOT native (`ocamlopt`) | same base flags | Single-process, single-threaded | Pure sequential; `unix.cmxa` linked but unused |
| OCaml (k-nucleotide) | AOT native (`ocamlopt`) | same base flags | Multi-process, Unix `fork` (7 children, fixed task list) | Results via `Marshal` over `Unix.pipe` |
| OCaml (mandelbrot) | AOT native (`ocamlopt`) | same base flags | Multi-process, Unix `fork` (64 workers, hardcoded) | Chain-fork pattern; each worker computes a row-band |
| OCaml (n-body) | AOT native (`ocamlopt`) | same base flags **minus** `-I +unix unix.cmxa` | Single-process, single-threaded | Only benchmark without unix library |
| OCaml (regex-redux) | AOT native (`ocamlfind ocamlopt`) | same base flags; `-package re`/`re.pcre` `-package unix -linkpkg` | Two-process, Unix `fork` (1 child) | Only benchmark using `ocamlfind`; uses pure-OCaml `re` library |
| OCaml (spectral-norm) | AOT native (`ocamlopt`) | same base flags | Single-process, single-threaded | Pure sequential; `unix.cmxa` linked but unused |
