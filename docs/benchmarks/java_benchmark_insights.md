# Java Benchmark Insights

**Language:** Java  
**Compilation:** GraalVM Native Image (AOT) — Community Edition  
**GraalVM/JDK version:** 23.0.2 (image `ghcr.io/graalvm/native-image-community:23.0.2`)  
**No JIT warmup:** All benchmarks are compiled ahead-of-time to native machine code. There is no JVM interpreter phase, no JIT compiler, and no warmup period. The binary starts at full-speed from the first instruction, which materially affects energy/time results relative to JVM/JIT runs — typically favouring Java AOT on short workloads while removing adaptive optimisation benefits on longer ones.

---

## binary-trees — Java

- **Execution:** AOT via GraalVM native-image 23.0.2 with `-O3 -march=native`; **GC = default** (no `--gc` flag — matches CLBG reference). `build_in_tmp.sh:12`.
- **Concurrency:** Multi-threaded. Uses `java.util.concurrent.ExecutorService` (`Executors.newFixedThreadPool`) sized to `Runtime.getRuntime().availableProcessors()`. Each tree-depth iteration is submitted as a task lambda; scales with available CPU cores. `Main.java:17–18, 38`.
- **Build/runtime config:**
  - `javac -d . -cp . Main.java` (`build_in_tmp.sh:10`)
  - `native-image --silent -cp . -O3 -march=native Main -o binarytrees.graalvmaot-7.graalvmaot_run` (`build_in_tmp.sh:12`)
  - No `--gc` flag; GraalVM Community defaults to its built-in serial GC.
  - Flow command: `binarytrees.graalvmaot-7.graalvmaot_run 21` (`binary-trees.yml:18`)
- **Source of flags:** `benchmarks/java/binary-trees/build_in_tmp.sh:12`

---

## fannkuch-redux — Java

- **Execution:** AOT via GraalVM native-image 23.0.2 with `-O3 -march=native`; **GC = G1** (fallback to `--gc=serial`). `build_in_tmp.sh:13–15`.
- **Concurrency:** Multi-threaded. Spawns `Runtime.getRuntime().availableProcessors()` `Thread` objects; each runs `Main.run()` which atomically claims work chunks from a shared `AtomicInteger taskId` (work-stealing style over `NCHUNKS=150` chunks). Scales with CPU cores. `Main.java:158–163, 124`.
- **Build/runtime config:**
  - `javac -d . -cp . Main.java` (`build_in_tmp.sh:10`)
  - `native-image --silent --gc=G1 -cp . -O3 -march=native Main -o fannkuchredux.graalvmaot_run` (fallback: `--gc=serial`) (`build_in_tmp.sh:13–15`)
  - Flow command: `fannkuchredux.graalvmaot_run 12` (`fannkuch-redux.yml:18`)
- **Source of flags:** `benchmarks/java/fannkuch-redux/build_in_tmp.sh:13–15`

---

## fasta — Java

- **Execution:** AOT via GraalVM native-image 23.0.2 with `-O3 -march=native`; **GC = G1** (fallback to `--gc=serial`). `build_in_tmp.sh:13–15`.
- **Concurrency:** Multi-threaded (producer–consumer pipeline). Creates `max(availableProcessors() - 1, 1)` daemon worker threads of type `NucleotideSelector extends Thread`, each with an `ArrayBlockingQueue` for in/out buffers. The main thread dispatches buffer fill jobs and collects results in round-robin fashion. Scales with CPU cores minus one. `Main.java:24–26, 38–43`.
- **Build/runtime config:**
  - `javac -d . -cp . Main.java` (`build_in_tmp.sh:10`)
  - `native-image --silent --gc=G1 -cp . -O3 -march=native Main -o fasta.graalvmaot-6.graalvmaot_run` (fallback: `--gc=serial`) (`build_in_tmp.sh:13–15`)
  - Flow command: `fasta.graalvmaot-6.graalvmaot_run 25000000` (`fasta.yml:18`)
- **Source of flags:** `benchmarks/java/fasta/build_in_tmp.sh:13–15`

---

## k-nucleotide — Java

- **Execution:** AOT via GraalVM native-image 23.0.2 with `-O3 -march=native`; **GC = G1** (fallback to `--gc=serial`). `build_in_tmp.sh:21–23`.
- **Concurrency:** Multi-threaded. Uses `ExecutorService` (`Executors.newFixedThreadPool(availableProcessors())`); invokes `invokeAll()` over a list of `Callable<Result>` tasks covering all fragment lengths and offsets (up to `sum(1..18)` = many tasks). Results are collected via `Future.get()`. Scales with CPU cores. `Main.java:160–164`.
- **Build/runtime config:**
  - Requires `fastutil-8.3.1.jar` (downloaded in `k-nucleotide.yml:11` setup-commands; verified present by `build_in_tmp.sh:11–14`).
  - `javac -d . -cp ".:fastutil-8.3.1.jar" Main.java` (`build_in_tmp.sh:18`)
  - `native-image --silent --gc=G1 -cp ".:fastutil-8.3.1.jar" -O3 -march=native Main -o knucleotide.graalvmaot_run` (fallback: `--gc=serial`) (`build_in_tmp.sh:21–23`)
  - Flow command: `knucleotide.graalvmaot_run 0 < /tmp/repo/inputs/fasta-2500000.txt` (`k-nucleotide.yml:21`)
- **Source of flags:** `benchmarks/java/k-nucleotide/build_in_tmp.sh:21–23`

---

## mandelbrot — Java

- **Execution:** AOT via GraalVM native-image 23.0.2 with `-O3 -march=native`; **GC = G1** (fallback to `--gc=serial`). `build_in_tmp.sh:13–15`.
- **Concurrency:** Multi-threaded. Creates `2 * Runtime.getRuntime().availableProcessors()` anonymous `Thread` objects; each claims rows via a shared `AtomicInteger yCt`. Scales with CPU cores (2× oversubscription). `Main.java:64–71`.
- **Build/runtime config:**
  - `javac -d . -cp . Main.java` (`build_in_tmp.sh:10`)
  - `native-image --silent --gc=G1 -cp . -O3 -march=native Main -o mandelbrot.graalvmaot-6.graalvmaot_run` (fallback: `--gc=serial`) (`build_in_tmp.sh:13–15`)
  - Flow command: `mandelbrot.graalvmaot-6.graalvmaot_run 16000` (`mandelbrot.yml:18`)
- **Source of flags:** `benchmarks/java/mandelbrot/build_in_tmp.sh:13–15`

---

## n-body — Java

- **Execution:** AOT via GraalVM native-image 23.0.2 with `-O3 -march=native`; **GC = G1** (fallback to `--gc=serial`). `build_in_tmp.sh:13–15`.
- **Concurrency:** Single-threaded. Pure sequential O(n²) simulation — nested loops over 5 bodies, no concurrency primitives used anywhere in the source. `Main.java:1–179`.
- **Build/runtime config:**
  - `javac -d . -cp . Main.java` (`build_in_tmp.sh:10`)
  - `native-image --silent --gc=G1 -cp . -O3 -march=native Main -o nbody.graalvmaot-4.graalvmaot_run` (fallback: `--gc=serial`) (`build_in_tmp.sh:13–15`)
  - Flow command: `nbody.graalvmaot-4.graalvmaot_run 50000000` (`n-body.yml:18`)
- **Source of flags:** `benchmarks/java/n-body/build_in_tmp.sh:13–15`

---

## regex-redux — Java

- **Execution:** AOT via GraalVM native-image 23.0.2 with `-O3 -march=native`; **GC = G1** (fallback to `--gc=serial`); plus FFI/experimental flags. `build_in_tmp.sh:66–82`.
- **Concurrency:** Multi-threaded. Uses a fixed-size `ExecutorService` (`Executors.newFixedThreadPool(availableProcessors())`). Nine regex-count tasks are submitted concurrently via `invokeAll()`; one substitution task is submitted via `submit()` independently. Scales with CPU cores. `Main.java:29–30, 46, 88–109`.
- **Build/runtime config:**
  - Setup downloads jextract-22 (build 6-47) for the target arch (linux-x64 or linux-aarch64), installs `libpcre2-dev` via `apt-get`/`microdnf`/`dnf`, and runs jextract to generate `jextract_pcre2` bindings into `jextract-classes/`. (`build_in_tmp.sh:5–53`)
  - `javac -d . -cp jextract-classes regexredux.java` (note: source is copied as `regexredux.java` to match public class name `regexredux`) (`build_in_tmp.sh:63`)
  - `native-image --silent --gc=G1 -H:+UnlockExperimentalVMOptions -H:+ForeignAPISupport --enable-native-access=ALL-UNNAMED --features=ForeignRegistrationFeature -Djava.library.path=<pcre2_lib_dir> -cp ".:jextract-classes" -O3 -march=native regexredux -o regexredux.graalvmaot-4.graalvmaot_run` (fallback: `--gc=serial`) (`build_in_tmp.sh:66–82`)
  - The `ForeignRegistrationFeature` class (defined in `Main.java:212–268`) registers all PCRE2 downcall descriptors at build time for native-image.
  - PCRE2 patterns are JIT-compiled at runtime via `pcre2_jit_compile_8`. (`Main.java:164–166`)
  - Flow command: `regexredux.graalvmaot-4.graalvmaot_run 0 < /tmp/repo/inputs/fasta-5000000.txt` (`regex-redux.yml:19`)
- **Source of flags:** `benchmarks/java/regex-redux/build_in_tmp.sh:66–82`

---

## spectral-norm — Java

- **Execution:** AOT via GraalVM native-image 23.0.2 with `-O3 -march=native`; **GC = G1** (fallback to `--gc=serial`). `build_in_tmp.sh:13–15`.
- **Concurrency:** Multi-threaded. Creates `NCPU = availableProcessors()` `Times extends Thread` objects per matrix-vector multiply call (two barrier-synchronized passes per `aTimesTransp` call, invoked 20 times total). Rows of the output vector are partitioned across threads. Scales with CPU cores. `Main.java:13, 37–50`.
- **Build/runtime config:**
  - `javac -d . -cp . Main.java` (`build_in_tmp.sh:10`)
  - `native-image --silent --gc=G1 -cp . -O3 -march=native Main -o spectralnorm.graalvmaot-3.graalvmaot_run` (fallback: `--gc=serial`) (`build_in_tmp.sh:13–15`)
  - Flow command: `spectralnorm.graalvmaot-3.graalvmaot_run 5500` (`spectral-norm.yml:18`)
- **Source of flags:** `benchmarks/java/spectral-norm/build_in_tmp.sh:13–15`

---

## Discrepancy log

One discrepancy found between `docs/flags.md` and the actual build scripts:

1. **`flags.md` description of `regex-redux` `-Djava.library.path`:** `flags.md:80` states the path as the literal string `Include/java/jextract_pcre2`, but `build_in_tmp.sh:56,71` dynamically resolves the path at build time using `find /usr/lib /lib -name 'libpcre2-8.so*'` and sets `PCRE2_LIB_DIR` to the directory of the found `.so`. The actual path passed is the real PCRE2 library directory (e.g. `/usr/lib/x86_64-linux-gnu`), not the literal string in the docs.

No other discrepancies found. All other flags in `flags.md` (binary-trees no-GC, G1/serial fallback for all others, fastutil jar for k-nucleotide, FFI flags for regex-redux) are confirmed accurate.

---

## Summary table row(s)

| Language | Compilation Type | Enabling Flags | Concurrency | Notes |
|---|---|---|---|---|
| Java | AOT (GraalVM native-image 23.0.2, Community) | `-O3 -march=native`; `--gc=G1` (fallback `--gc=serial`) for all benchmarks except binary-trees (no `--gc`); regex-redux adds `-H:+UnlockExperimentalVMOptions -H:+ForeignAPISupport --enable-native-access=ALL-UNNAMED --features=ForeignRegistrationFeature` | Multi-threaded for all benchmarks except n-body (single); mechanism varies: `ExecutorService`/`Executors.newFixedThreadPool(availableProcessors())` for binary-trees, k-nucleotide, regex-redux; raw `Thread[]` with `AtomicInteger` work-stealing for fannkuch-redux and mandelbrot (2× oversubscription); producer–consumer `Thread`+`ArrayBlockingQueue` for fasta (nCPU−1 workers); `Thread[]` partitioned by row for spectral-norm; scales with available CPU cores in all multi-threaded cases | No JIT warmup (AOT binary). k-nucleotide links fastutil-8.3.1.jar. regex-redux uses jextract-22 (build 6-47) to generate PCRE2 FFI bindings via Panama Foreign API; PCRE2 patterns JIT-compiled at runtime via `pcre2_jit_compile_8`. GraalVM Community image lacks G1 GC support in practice — `--gc=serial` fallback applies on this image. |
