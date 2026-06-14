# PHP Benchmark Insights

**Language:** PHP  
**Version:** 8.4 (image `php:8.4-cli`; wrapper probes `/opt/src/php-8.4.1/bin/php` first, falls back to system `php`)  
**Execution model:** Interpreted — Zend VM with OPcache opcode caching; **JIT is off**. The wrappers load `opcache.so` and pass `-dopcache.jit_buffer_size=64M`, but never set the `opcache.jit` mode, so PHP 8.4 leaves JIT disabled and the buffer unused (verified: `opcache_get_status()` reports `jit.on = false`, `buffer_size = 0`). Classified as Interpreted to match the CLBG convention. No separate compile step — `build_in_tmp.sh` generates a shell wrapper at `/tmp/php-<bench>` that embeds all flags at setup time.  
**Base OPcache flags (all benchmarks):** `-dzend_extension=<opcache.so> -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n` (opcode cache only; no `opcache.jit` mode → no JIT)

---

## Per-Benchmark Breakdown

> **Binary-Trees — PHP**
> - **Execution:** Interpreted (Zend VM + OPcache opcode cache; JIT off) with OPcache loaded via `-dzend_extension=<opcache.so> -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -dextension=shmop -dextension=pcntl -d memory_limit=4096M` (fallback: interpreted with `-n -dextension=shmop -dextension=pcntl -d memory_limit=4096M`)
> - **Concurrency:** Multi-process. One worker forked per tree-depth level via `pcntl_fork` (fork loop at `main.php:48`). Total workers = `count($depthIterations)` — for N=21 this is 9 depth levels (`minDepth=4` to `maxDepth=21` in steps of 2, `main.php:64-72`). Workers do not scale dynamically with CPU count; the count is fixed by the depth range. IPC via shared memory: each child writes its result string to a fixed-size slot in a `shmop` segment (`main.php:59, 75`); parent reads slots after joining all children (`main.php:84-86`).
> - **Build/runtime config:** OPcache JIT buffer 64 MB (allocated but unused — JIT off); memory limit 4096 MB; extensions `shmop` and `pcntl` loaded via CLI flags. Extensions also installed in the container image via `docker-php-ext-install` (`binary-trees.yml:10`).
> - **Source of flags:** `benchmarks/php/binary-trees/build_in_tmp.sh:36-38` (wrapper generation); `benchmarks/php/binary-trees/binary-trees.yml:10-11` (image setup); `benchmarks/php/binary-trees/main.php:48,59,75` (fork and shmop usage).

---

> **Fannkuch-Redux — PHP**
> - **Execution:** Interpreted (Zend VM + OPcache opcode cache; JIT off) with OPcache loaded via `-dzend_extension=<opcache.so> -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -dextension=shmop -dextension=pcntl` (fallback: interpreted with `-n -dextension=shmop -dextension=pcntl`)
> - **Concurrency:** Multi-process. Worker count = 2× logical CPU count (`$procs <<= 1`, `main.php:17-20`), derived from `/proc/cpuinfo` processor entries. Forks `$procs - 1` child processes (`main.php:39-48`); the last "proc" slot runs in the parent. Each worker owns a contiguous range of permutation indices. IPC via shared memory: each process writes a packed 16-byte result (maxflips + checksum) to its slot in a `shmop` segment (`main.php:134`); parent aggregates after `pcntl_wait` loop (`main.php:141-154`). Scales with CPU count.
> - **Build/runtime config:** OPcache JIT buffer 64 MB (allocated but unused — JIT off); no extra memory limit; `shmop` and `pcntl` loaded via CLI flags. No per-benchmark memory override.
> - **Source of flags:** `benchmarks/php/fannkuch-redux/build_in_tmp.sh:37-39`; `benchmarks/php/fannkuch-redux/main.php:17-20` (CPU detection), `main.php:39-48` (fork), `main.php:134` (shmop write).

---

> **Fasta — PHP**
> - **Execution:** Interpreted (Zend VM + OPcache opcode cache; JIT off) with OPcache loaded via `-dzend_extension=<opcache.so> -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n` (fallback: interpreted with `-n`). No extension flags loaded in the wrapper.
> - **Concurrency:** Single-process. No `pcntl_fork` anywhere in `main.php`. Output is generated sequentially.
> - **Build/runtime config:** OPcache JIT buffer 64 MB (allocated but unused — JIT off); no memory limit override; no extensions explicitly loaded in the CLI wrapper. Container setup installs `shmop` and `pcntl` (`fasta.yml:10`) but neither is loaded in the wrapper nor used in the source.
> - **Source of flags:** `benchmarks/php/fasta/build_in_tmp.sh:27-29`; `benchmarks/php/fasta/main.php` (no fork).

---

> **K-Nucleotide — PHP**
> - **Execution:** Interpreted (Zend VM + OPcache opcode cache; JIT off) with OPcache loaded via `-dzend_extension=<opcache.so> -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -d short_open_tag=1 -dextension=pcntl -dextension=sysvmsg -d memory_limit=1024M` (fallback: interpreted with `-n -d short_open_tag=1 -dextension=pcntl -dextension=sysvmsg -d memory_limit=1024M`). `-d short_open_tag=1` required because source opens with `<?` (`main.php:1`).
> - **Concurrency:** Multi-process. 7 jobs defined (`main.php:15-23`); `count($jobs) - 1 = 6` children forked (`main.php:30-39`), parent handles job 0. Each worker runs one job and sends its buffered output via a `sysvmsg` message queue (`main.php:53`); parent receives all 7 results and re-orders by index (`main.php:63-66`). Fixed at 6 workers regardless of CPU count.
> - **Build/runtime config:** OPcache JIT buffer 64 MB (allocated but unused — JIT off); memory limit 1024 MB; `pcntl` and `sysvmsg` loaded via CLI flags; `short_open_tag=1` enabled. Extensions also installed via `docker-php-ext-install` (`k-nucleotide.yml:10`).
> - **Source of flags:** `benchmarks/php/k-nucleotide/build_in_tmp.sh:37-39`; `benchmarks/php/k-nucleotide/main.php:1` (short tag), `main.php:25-39` (fork), `main.php:53` (sysvmsg send).

---

> **Mandelbrot — PHP**
> - **Execution:** Interpreted (Zend VM + OPcache opcode cache; JIT off) with OPcache loaded via `-dzend_extension=<opcache.so> -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -d short_open_tag=1 -dextension=shmop -dextension=pcntl` (fallback: interpreted with `-n -d short_open_tag=1 -dextension=shmop -dextension=pcntl`). `-d short_open_tag=1` required because source opens with `<?` (`main.php:1`).
> - **Concurrency:** Multi-process. Worker count = 2× logical CPU count (`$procs <<= 1`, `main.php:14-16`), derived from `/proc/cpuinfo`. Forks `$procs - 1` children (`main.php:47-57`); child index identifies which interleaved rows to compute (`y = child, step = procs`, `main.php:59-62`). IPC via shared memory: each process writes its computed bitmap rows to the appropriate offsets in a `shmop` segment (`main.php:98`); parent reads and outputs the full buffer after joining children (`main.php:111-114`). Scales with CPU count.
> - **Build/runtime config:** OPcache JIT buffer 64 MB (allocated but unused — JIT off); no extra memory limit; `shmop` and `pcntl` loaded via CLI flags; `short_open_tag=1` enabled.
> - **Source of flags:** `benchmarks/php/mandelbrot/build_in_tmp.sh:37-39`; `benchmarks/php/mandelbrot/main.php:14-16` (CPU detection), `main.php:47-57` (fork), `main.php:98` (shmop write).

---

> **N-Body — PHP**
> - **Execution:** Interpreted (Zend VM + OPcache opcode cache; JIT off) with OPcache loaded via `-dzend_extension=<opcache.so> -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -d short_open_tag=1` (fallback: interpreted with `-n -d short_open_tag=1`). `-d short_open_tag=1` required because source opens with `<?` (`main.php:1`). No extension flags loaded.
> - **Concurrency:** Single-process. No `pcntl_fork` in `main.php`. Pure sequential simulation over 5 bodies.
> - **Build/runtime config:** OPcache JIT buffer 64 MB (allocated but unused — JIT off); no memory limit override; no extensions explicitly loaded in the CLI wrapper. Container setup installs `shmop pcntl sysvmsg` (`n-body.yml:10`) but none are loaded in the wrapper or used in the source.
> - **Source of flags:** `benchmarks/php/n-body/build_in_tmp.sh:27-29`; `benchmarks/php/n-body/main.php` (no fork, no IPC).

---

> **Regex-Redux — PHP**
> - **Execution:** Interpreted (Zend VM + OPcache opcode cache; JIT off) with OPcache loaded via `-dzend_extension=<opcache.so> -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -dextension=pcntl -dextension=sysvmsg -d memory_limit=512M` (fallback: interpreted with `-n -dextension=pcntl -dextension=sysvmsg -d memory_limit=512M`)
> - **Concurrency:** Multi-process. 4 children forked at variant keys 0, 2, 4, 6 (`main.php:48-49`); each child handles 2 regex variants (keys N and N+1) and sends results via `sysvmsg` (`main.php:60`). Parent handles the 9th variant (key 8) and the final IUB replacements. Fixed at 4 child workers, does not scale with CPU count.
> - **Build/runtime config:** OPcache JIT buffer 64 MB (allocated but unused — JIT off); memory limit 512 MB; `pcntl` and `sysvmsg` loaded via CLI flags. Extensions also installed via `docker-php-ext-install` (`regex-redux.yml:10`).
> - **Source of flags:** `benchmarks/php/regex-redux/build_in_tmp.sh:37-39`; `benchmarks/php/regex-redux/main.php:48-62` (fork and sysvmsg).

---

> **Spectral-Norm — PHP**
> - **Execution:** Interpreted (Zend VM + OPcache opcode cache; JIT off) with OPcache loaded via `-dzend_extension=<opcache.so> -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -d short_open_tag=1 -dextension=pcntl` (fallback: interpreted with `-n -d short_open_tag=1 -dextension=pcntl`). `-d short_open_tag=1` required because source opens with `<?` (`main.php:1`).
> - **Concurrency:** Multi-process. Worker count derived from `/proc/cpuinfo` processor count (no doubling; `$procs` is direct count, `main.php:99-101`), capped to 1 if `n < procs` (`main.php:103-105`). Forks `$procs - 1` children (`main.php:114-131`); each owns a row-range chunk. IPC via Unix stream socket pairs (`pipe()` = `stream_socket_pair`, `main.php:92-93`): children write partial vectors to their pipe; parent reads all children's chunks, merges, and broadcasts the full vector back. The `sync()` function implements this barrier (`main.php:51-72`). Scales with CPU count (no ×2 doubling unlike fannkuch/mandelbrot).
> - **Build/runtime config:** OPcache JIT buffer 64 MB (allocated but unused — JIT off); no extra memory limit; `pcntl` loaded via CLI flags; `short_open_tag=1` enabled. Container setup installs `shmop pcntl sysvmsg` (`spectral-norm.yml:10`) but only `pcntl` is loaded in the wrapper; `shmop` and `sysvmsg` are unused.
> - **Source of flags:** `benchmarks/php/spectral-norm/build_in_tmp.sh:32-34`; `benchmarks/php/spectral-norm/main.php:99-101` (CPU detection), `main.php:114-131` (fork), `main.php:51-72` (pipe-based sync).

---

## Discrepancy Log

1. **Fannkuch-Redux — flags.md omits extension flags.** `flags.md` lists no extra flags for fannkuch-redux, but `build_in_tmp.sh:37` loads `-dextension=shmop` and `-dextension=pcntl`. `main.php` uses `shmop_open`/`shmop_write`, so these are required. `flags.md:202` is inaccurate for this benchmark.

2. **K-Nucleotide — `short_open_tag` not in flags.md.** `build_in_tmp.sh:37` adds `-d short_open_tag=1`. `flags.md` does not document this. Required because `main.php:1` uses `<?` short open tag.

3. **Mandelbrot — `short_open_tag` not in flags.md.** `build_in_tmp.sh:37` adds `-d short_open_tag=1`. `flags.md` does not document this. Required because `main.php:1` uses `<?`.

4. **N-Body — `short_open_tag` not in flags.md; YML installs unused extensions.** `build_in_tmp.sh:27` adds `-d short_open_tag=1` (not documented). `n-body.yml:10` installs `shmop pcntl sysvmsg` but none are used in `main.php` or loaded in the wrapper. `flags.md` makes no mention of these.

5. **Spectral-Norm — `short_open_tag` not in flags.md; YML installs shmop+sysvmsg unnecessarily.** `build_in_tmp.sh:32` adds `-d short_open_tag=1` (undocumented). `spectral-norm.yml:10` installs `shmop pcntl sysvmsg`, but `build_in_tmp.sh` only loads `pcntl`. Source uses Unix socket pipes, not shmop/sysvmsg.

6. **Fasta — YML installs shmop+pcntl but wrapper does not load them.** `fasta.yml:10` installs `shmop pcntl` via `docker-php-ext-install`. `build_in_tmp.sh` generates no `-dextension` flags. Source is single-threaded. These extensions are installed but have no effect. `flags.md` correctly lists no extensions for fasta but does not note the superfluous install.

7. **N-Body and Spectral-Norm CPU-count scaling note.** Spectral-norm does NOT double the CPU count (unlike fannkuch-redux and mandelbrot), so it uses 1× logical CPUs. `flags.md` does not document this difference.

---

## Summary Table Row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|----------|-----------------|----------------|-------------|-------|
| PHP (binary-trees) | Interpreted (Zend VM + OPcache opcode cache; JIT off, 64M buffer unused) | `-dzend_extension=opcache.so -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n` | Multi-process: `pcntl_fork` per depth level (fixed count, not CPU-scaled); IPC via `shmop` | `-d memory_limit=4096M`; loads `shmop`, `pcntl` |
| PHP (fannkuch-redux) | Interpreted (Zend VM + OPcache opcode cache; JIT off, 64M buffer unused) | `-dzend_extension=opcache.so -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n` | Multi-process: 2× CPU count workers via `pcntl_fork`; IPC via `shmop` | CPU-scaled (×2); loads `shmop`, `pcntl`; flags.md omits extension flags |
| PHP (fasta) | Interpreted (Zend VM + OPcache opcode cache; JIT off, 64M buffer unused) | `-dzend_extension=opcache.so -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n` | Single-process | No extensions loaded in wrapper; shmop+pcntl installed in container but unused |
| PHP (k-nucleotide) | Interpreted (Zend VM + OPcache opcode cache; JIT off, 64M buffer unused) | `-dzend_extension=opcache.so -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -d short_open_tag=1` | Multi-process: 6 fixed child workers via `pcntl_fork`; IPC via `sysvmsg` message queue | `-d memory_limit=1024M`; loads `pcntl`, `sysvmsg`; `short_open_tag` undocumented |
| PHP (mandelbrot) | Interpreted (Zend VM + OPcache opcode cache; JIT off, 64M buffer unused) | `-dzend_extension=opcache.so -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -d short_open_tag=1` | Multi-process: 2× CPU count workers via `pcntl_fork`; IPC via `shmop` | CPU-scaled (×2); loads `shmop`, `pcntl`; `short_open_tag` undocumented |
| PHP (n-body) | Interpreted (Zend VM + OPcache opcode cache; JIT off, 64M buffer unused) | `-dzend_extension=opcache.so -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -d short_open_tag=1` | Single-process | No extensions loaded; shmop+pcntl+sysvmsg installed in container but unused; `short_open_tag` undocumented |
| PHP (regex-redux) | Interpreted (Zend VM + OPcache opcode cache; JIT off, 64M buffer unused) | `-dzend_extension=opcache.so -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n` | Multi-process: 4 fixed child workers via `pcntl_fork`; IPC via `sysvmsg` message queue | `-d memory_limit=512M`; loads `pcntl`, `sysvmsg` |
| PHP (spectral-norm) | Interpreted (Zend VM + OPcache opcode cache; JIT off, 64M buffer unused) | `-dzend_extension=opcache.so -dopcache.enable_cli=1 -dopcache.jit_buffer_size=64M -n -d short_open_tag=1` | Multi-process: 1× CPU count workers via `pcntl_fork`; IPC via Unix socket pipes | CPU-scaled (×1, no doubling); loads `pcntl` only; `short_open_tag` undocumented; shmop+sysvmsg installed but unused |
