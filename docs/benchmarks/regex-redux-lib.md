# Regex-Redux: Regex Engine Audit per Language

Audit date: 2026-11-07

## Purpose

Regex-redux spends almost all of its time inside a regular expression engine, so the measured energy and time reflect the engine more than the host language. This report identifies, for each of the 18 languages, which engine the benchmark actually calls, whether that engine is a third party library (usually PCRE or PCRE2), and whether the engine is written in the benchmark's own language or is a foreign C/C++ library reached through bindings.

## Method

For each language, three things were checked:

1. **Install proof**, the line in `benchmarks/<lang>/regex-redux.yml` or `build_in_tmp.sh` that installs or links the library.
2. **Usage proof**, the line in the benchmark source that calls the engine.
3. **Engine language proof**, an official external source (project README, docs, or source tree) showing what language the engine is implemented in. External URLs are listed per language and again in the Sources section.

Anything that could not be confirmed from these sources is marked **unverified**.

## Summary

| Lang | Engine | Kind | Engine language |
|---|---|---|---|
| C | PCRE2 (`libpcre2-8`) | 3rd party | C |
| C++ | PCRE2 (`libpcre2-8`) | 3rd party | C |
| C# | PCRE2 (`libpcre2-8`) via P/Invoke | 3rd party | C |
| Dart | Dart VM `RegExp` (port of V8 Irregexp) | Runtime builtin | C++ |
| Erlang | `re` module (PCRE2 bundled in ERTS) | Stdlib, bundled 3rd party | C |
| F# | .NET `System.Text.RegularExpressions` | Stdlib | C# |
| Go | PCRE 1 (8.x) via `github.com/GRbit/go-pcre` (cgo) | 3rd party | C |
| Haskell | PCRE2 (`libpcre2-8`) via hand written FFI | 3rd party | C |
| Java | PCRE2 (`libpcre2-8`) via jextract / Panama FFM | 3rd party | C |
| JavaScript (Node.js) | V8 Irregexp | Runtime builtin | C++ |
| Lua | PCRE2 via `lrexlib-pcre2` (`rex_pcre2`) | 3rd party | C |
| OCaml | `re` (ocaml-re), used through its `Re.Pcre` interface | 3rd party (opam) | OCaml |
| Perl | Perl core regex engine | Builtin | C |
| PHP | `preg_*` (PCRE2 bundled in `ext/pcre`) | Builtin, bundled 3rd party | C |
| Python | PCRE2 (`libpcre2-8`) via `ctypes` | 3rd party | C |
| Ruby | Onigmo (CRuby builtin) | Builtin | C |
| Rust | PCRE2 via `pcre2-sys` crate | 3rd party | C |
| Swift | `NSRegularExpression` (Foundation, backed by ICU `uregex`) | Stdlib wrapping 3rd party | C/C++ |

### Grouped view

**Foreign C PCRE called through a binding (10 languages).** C, C++, C#, Go, Haskell, Java, Lua, Python and Rust call the C PCRE library directly or through an FFI layer. All use PCRE2 except Go, which uses the older PCRE 1 (8.x). None of these languages use their own standard library regex engine for this benchmark.

**Engine bundled inside the runtime, written in C or C++ (7 languages).** Erlang and PHP ship a private copy of PCRE2 inside the VM or interpreter. Node.js and Dart use Irregexp (Dart's copy is a port of V8's). Perl and Ruby use their own C engines (Perl core engine, Onigmo). Swift's Foundation delegates to ICU.

**Engine written in the benchmark's own language (2 languages).** Only OCaml (`re`, pure OCaml) and F# (`System.Text.RegularExpressions`, written in C#, which shares the .NET runtime and IL with F#) run an engine implemented in their own ecosystem. Strictly, F#'s engine is written in C#, not F#, but it runs as managed .NET code with no native regex library underneath.

## Per-language audit

### C

PCRE2, a C library, linked directly. Foreign to nothing, since C is the engine's own language.

**Evidence**
- Install: [c/regex-redux.yml:9](../../benchmarks/c/regex-redux.yml) links with `-lpcre2-8`. No explicit package install, so the shared library comes from the `gcc:15.2.0` base image (which package provides it is **unverified**).
- Header: [c/regex-redux/pcre2.h:44](../../benchmarks/c/regex-redux/pcre2.h) is a vendored PCRE2 header, `#define PCRE2_MAJOR 10`, `PCRE2_MINOR 33`.
- Usage: [c/regex-redux/main.c:12](../../benchmarks/c/regex-redux/main.c) `#include "pcre2.h"`, [main.c:32](../../benchmarks/c/regex-redux/main.c) `pcre2_compile(...)`, [main.c:181](../../benchmarks/c/regex-redux/main.c) `pcre2_compile(...)` (pattern counting).
- Engine language: PCRE2 is a C library, https://github.com/PCRE2Project/pcre2

### C++

PCRE2 (C) wrapped in a small C++ RAII class. Boost is installed only for `boost::noncopyable`, it plays no role in matching. Engine is foreign C, though C is directly callable from C++.

**Evidence**
- Install: [cpp/regex-redux.yml:10](../../benchmarks/cpp/regex-redux.yml) installs `libboost-dev`; [cpp/regex-redux.yml:11](../../benchmarks/cpp/regex-redux.yml) links `-lpcre2-8`.
- Header: [cpp/regex-redux/pcre2.h:44](../../benchmarks/cpp/regex-redux/pcre2.h), vendored PCRE2 10.33 header.
- Usage: [cpp/regex-redux/main.cpp:15](../../benchmarks/cpp/regex-redux/main.cpp) `#include <boost/noncopyable.hpp>`, [main.cpp:24](../../benchmarks/cpp/regex-redux/main.cpp) `#include "pcre2.h"`, [main.cpp:43](../../benchmarks/cpp/regex-redux/main.cpp) `class regex : private boost::noncopyable`, [main.cpp:222](../../benchmarks/cpp/regex-redux/main.cpp) `pcre2_compile(...)`.
- Engine language: https://github.com/PCRE2Project/pcre2

### C#

Does **not** use .NET `System.Text.RegularExpressions`. Calls native PCRE2 through P/Invoke. Foreign C library.

**Evidence**
- Install: [csharp/regex-redux.yml:11](../../benchmarks/csharp/regex-redux.yml) `apt-get install ... libpcre2-dev`.
- Usage: [csharp/regex-redux/main.cs:142](../../benchmarks/csharp/regex-redux/main.cs) `[DllImport("pcre2-8", EntryPoint = "pcre2_compile_8", ...)]`, with further imports of `pcre2_match_data_create_8`, `pcre2_substitute_8` and others at lines 146 to 162.
- Engine language: https://github.com/PCRE2Project/pcre2

### Dart

Uses the language's built in `RegExp`. The Dart VM implementation is a port of V8's Irregexp, written in C++. Not a third party package, but not written in Dart either.

**Evidence**
- Install: none, [dart/regex-redux.yml:9](../../benchmarks/dart/regex-redux.yml) only runs `dart compile exe`.
- Usage: [dart/regex-redux/main.dart:15](../../benchmarks/dart/regex-redux/main.dart) `RegExp('>.*\n|\n', multiLine: true)`, [main.dart:45](../../benchmarks/dart/regex-redux/main.dart), [main.dart:60](../../benchmarks/dart/regex-redux/main.dart).
- Engine language: the Dart SDK directory `runtime/vm/regexp` contains only `.cc`/`.h` files, and its README states the Dart VM implementation "is taken from V8, which is called Irregexp". https://github.com/dart-lang/sdk/tree/main/runtime/vm/regexp

### Erlang

Uses the standard library `re` module. Since OTP 28 it is backed by a copy of PCRE2 compiled into the Erlang runtime (ERTS). The benchmark uses OTP 29. Engine is C, bundled in the VM, no external package.

**Evidence**
- Install: none, [erlang/regex-redux.yml:7](../../benchmarks/erlang/regex-redux.yml) uses image `erlang:29.0.0`.
- Usage: [erlang/regex-redux/regexredux.erl:38](../../benchmarks/erlang/regex-redux/regexredux.erl) `re:compile(Pat, [caseless])`, [regexredux.erl:56](../../benchmarks/erlang/regex-redux/regexredux.erl) `re:replace(...)`, [regexredux.erl:70](../../benchmarks/erlang/regex-redux/regexredux.erl) `re:run(...)`.
- Engine language: OTP `re` docs state PCRE2 is used ("Currently PCRE2 version 10.45 ... is used") and that the switch to PCRE2 happened starting with Erlang/OTP 28. https://www.erlang.org/doc/apps/stdlib/re.html

### F#

Uses .NET `System.Text.RegularExpressions.Regex` with `RegexOptions.Compiled`. This is the one .NET entry that does not call PCRE2, unlike the C# benchmark. The engine is managed code written in C#, part of the .NET runtime libraries.

**Evidence**
- Install: none, [fsharp/regex-redux.yml](../../benchmarks/fsharp/regex-redux.yml) only runs the shared build script. Side note: [fsharp/build_common.sh:59](../../benchmarks/fsharp/build_common.sh) sets `<PublishAot>false</PublishAot>`, so F# runs on the CLR rather than as a Native AOT binary as `CLAUDE.md` states.
- Usage: [fsharp/regex-redux/main.fs:9](../../benchmarks/fsharp/regex-redux/main.fs) `open System.Text.RegularExpressions`, [main.fs:11](../../benchmarks/fsharp/regex-redux/main.fs) `Regex(s, RegexOptions.Compiled)`.
- Engine language: the `System.Text.RegularExpressions` source tree in dotnet/runtime is all `.cs` (for example `RegexInterpreter.cs`, `RegexCompiler.cs`). https://github.com/dotnet/runtime/tree/main/src/libraries/System.Text.RegularExpressions/src/System/Text/RegularExpressions

### Go

Does **not** use Go's standard `regexp` package (which is pure Go). Uses `github.com/GRbit/go-pcre`, a cgo binding to the legacy C PCRE 1 (8.x) library, not PCRE2. This makes Go the only PCRE 1 user among the 18 languages.

**Evidence**
- Install: [go/regex-redux.yml:10](../../benchmarks/go/regex-redux.yml) `apk add --no-cache gcc musl-dev pcre-dev` (Alpine `pcre-dev` is PCRE 1); [go/regex-redux.yml:12](../../benchmarks/go/regex-redux.yml) `go get github.com/GRbit/go-pcre@v1.0.0`.
- Usage: [go/regex-redux/main.go:19](../../benchmarks/go/regex-redux/main.go) `"github.com/GRbit/go-pcre"`, [main.go:28](../../benchmarks/go/regex-redux/main.go) `pcre.MustCompile...(...)` (compiles a PCRE pattern).
- Engine language: go-pcre README, "This project depends on the original PCRE library rather than PCRE2", refers to "PCRE 8.x", and "Since this package use cgo it will build dynamically linked." https://github.com/GRbit/go-pcre

### Haskell

No Haskell package is used. The benchmark declares its own `foreign import ccall` bindings to PCRE2 and links `-lpcre2-8`. The source itself comments that Haskell lacks a proper PCRE2 binding. Foreign C library.

**Evidence**
- Install: [haskell/regex-redux.yml:10](../../benchmarks/haskell/regex-redux.yml) installs `libpcre2-dev`; [haskell/regex-redux.yml:14](../../benchmarks/haskell/regex-redux.yml) builds with `-XForeignFunctionInterface -XCApiFFI ... -lpcre2-8`.
- Usage: [haskell/regex-redux/main.hs:23](../../benchmarks/haskell/regex-redux/main.hs) `-- first some foreign imports (Haskell does not have a proper pcre2 binding!)`, [main.hs:31](../../benchmarks/haskell/regex-redux/main.hs) `foreign import ccall "pcre2.h pcre2_compile_8"`.
- Engine language: https://github.com/PCRE2Project/pcre2

### Java

Does **not** use `java.util.regex`. Generates Java bindings for `pcre2.h` with jextract and calls native PCRE2 through the Foreign Function and Memory API inside the GraalVM native image. Foreign C library.

**Evidence**
- Install: [java/regex-redux/build_in_tmp.sh:22](../../benchmarks/java/regex-redux/build_in_tmp.sh) installs `libpcre2-dev`; [build_in_tmp.sh:48-53](../../benchmarks/java/regex-redux/build_in_tmp.sh) runs jextract with `-l pcre2-8 /usr/include/pcre2.h -t jextract_pcre2`.
- Usage: [java/regex-redux/Main.java:8](../../benchmarks/java/regex-redux/Main.java) `import jextract_pcre2.pcre2_h;`, [Main.java:156](../../benchmarks/java/regex-redux/Main.java) `pcre2_h.pcre2_compile_8(...)`, [Main.java:136](../../benchmarks/java/regex-redux/Main.java) `pcre2_h.pcre2_substitute_8(...)`.
- Engine language: https://github.com/PCRE2Project/pcre2

### JavaScript (Node.js)

Uses JavaScript regex literals, executed by V8's Irregexp engine. Built into the runtime, written in C++, not JavaScript.

**Evidence**
- Install: none, [nodejs/regex-redux.yml:7](../../benchmarks/nodejs/regex-redux.yml) uses image `node:25-alpine3.21` with no setup.
- Usage: [nodejs/regex-redux/main.js:37](../../benchmarks/nodejs/regex-redux/main.js) `data.replace(/^>.*\n|\n/mg, '')`, [main.js:44](../../benchmarks/nodejs/regex-redux/main.js) `data.match(re)`, [main.js:64-68](../../benchmarks/nodejs/regex-redux/main.js).
- Engine language: V8 blog, "RegExp matching in V8 is handled by the Irregexp engine." https://v8.dev/blog/non-backtracking-regexp . V8 is a C++ codebase, https://github.com/v8/v8/tree/main/src/regexp

### Lua

Lua has no regex in its standard library (only Lua patterns). The benchmark uses `lrexlib-pcre2` from LuaRocks, a C module binding the C PCRE2 library. Foreign C library.

**Evidence**
- Install: [lua/regex-redux.yml:10](../../benchmarks/lua/regex-redux.yml) `apk add ... pcre2-dev` and `luarocks install lrexlib-pcre2`; [lua/regex-redux/build_in_tmp.sh:4](../../benchmarks/lua/regex-redux/build_in_tmp.sh) checks `require("rex_pcre2")`.
- Usage: [lua/regex-redux/main.lua:20](../../benchmarks/lua/regex-redux/main.lua) `Lrexlib_PCRE2=require("rex_pcre2")`, [main.lua:30](../../benchmarks/lua/regex-redux/main.lua) `Lrexlib_PCRE2.new(...)`.
- Engine language: lrexlib README, "A Lua (5.1 and later) binding of various regex library APIs", with PCRE2 listed as a flavour. https://github.com/rrthomas/lrexlib

### OCaml

Uses the opam package `re` (ocaml-re). Despite the `Re.Pcre` module name, there is no PCRE underneath, `Re.Pcre` is only a PCRE style interface over a pure OCaml engine. This is the only benchmark whose engine is written in the language being measured.

**Evidence**
- Install: [ocaml/regex-redux.yml:10](../../benchmarks/ocaml/regex-redux.yml) `opam install -y ocamlfind re`; [ocaml/regex-redux/build_in_tmp.sh:15-16](../../benchmarks/ocaml/regex-redux/build_in_tmp.sh) selects package `re.pcre`. No PCRE system package is installed.
- Usage: [ocaml/regex-redux/main.ml:32](../../benchmarks/ocaml/regex-redux/main.ml) `Re.replace_string (Re.Pcre.regexp ">.*\n|\n") ...`, [main.ml:42](../../benchmarks/ocaml/regex-redux/main.ml) `Re.exec`.
- Engine language: ocaml-re describes itself as "Pure OCaml regular expressions", README says "The library is at the moment entirely written in OCaml", and `Re.Pcre` offers "a subset of the PCRE interface". https://github.com/ocaml/ocaml-re

### Perl

Uses Perl's built in regex operators (`=~`, `s///`, `qr//`). The engine is part of the perl interpreter, written in C. No external library.

**Evidence**
- Install: none, [perl/regex-redux.yml:7](../../benchmarks/perl/regex-redux.yml) uses `perl:5.42.1-threaded` with no setup.
- Usage: [perl/regex-redux/main.pl:27](../../benchmarks/perl/regex-redux/main.pl) `$seq =~ /$patterns->[$i]/g`, [main.pl:46](../../benchmarks/perl/regex-redux/main.pl) `qr/$_/iaa`, [main.pl:60](../../benchmarks/perl/regex-redux/main.pl) `$seq =~ s/>.*\n|\n//g`.
- Engine language: perlreguts, "This code resides primarily in regcomp.c, along with the header files regcomp.h, regexp.h and regnodes.h." https://perldoc.perl.org/perlreguts

### PHP

Uses the core `preg_*` functions from `ext/pcre`. By default PHP compiles in its own bundled copy of PCRE2. The official `php:8.4-cli` image's `./configure` line has no `--with-external-pcre`, so the bundled copy is used. C library, bundled in the interpreter.

**Evidence**
- Install: none for PCRE, [php/regex-redux.yml:7](../../benchmarks/php/regex-redux.yml) uses `php:8.4-cli`; setup only adds `shmop pcntl sysvmsg`.
- Usage: [php/regex-redux/main.php:41](../../benchmarks/php/regex-redux/main.php) `preg_replace(...)`, [main.php:54](../../benchmarks/php/regex-redux/main.php) `preg_match_all(...)`, [main.php:81](../../benchmarks/php/regex-redux/main.php).
- Engine language: PHP manual, "By default, the extension uses a bundled version of the PCRE2 library", "The PCRE extension is a core PHP extension and is always enabled". https://www.php.net/manual/en/pcre.installation.php . Docker image configure flags (no `--with-external-pcre`): https://github.com/docker-library/php/blob/master/8.4/bookworm/cli/Dockerfile

### Python

Does **not** use the standard `re` module. Loads `libpcre2-8` at runtime through `ctypes` and calls the PCRE2 C API directly. Foreign C library.

**Evidence**
- Install: [python/regex-redux.yml:10](../../benchmarks/python/regex-redux.yml) `apt-get install ... libpcre2-8-0`.
- Usage: [python/regex-redux/main.py:23](../../benchmarks/python/regex-redux/main.py) `PCRE2=CDLL(find_library("pcre2-8"))`, [main.py:41](../../benchmarks/python/regex-redux/main.py) `PCRE2.pcre2_compile_8(...)`, [main.py:50](../../benchmarks/python/regex-redux/main.py) `PCRE2.pcre2_substitute_8(...)`.
- Engine language: https://github.com/PCRE2Project/pcre2

### Ruby

Uses Ruby regex literals with `String#scan` and `String#gsub!`. CRuby's engine is Onigmo, written in C and compiled into the interpreter. Onigmo started as a third party fork of Oniguruma but ships inside CRuby, so no external install is needed.

**Evidence**
- Install: none, [ruby/regex-redux.yml:7](../../benchmarks/ruby/regex-redux.yml) uses `ruby:3.4`.
- Usage: [ruby/regex-redux/main.rb:9-19](../../benchmarks/ruby/regex-redux/main.rb) regex literals, [main.rb:49](../../benchmarks/ruby/regex-redux/main.rb) `@seq.scan(regex)`, [main.rb:73](../../benchmarks/ruby/regex-redux/main.rb) `@seq.gsub!(/>.*\n|\n/, '')`.
- Engine language: Onigmo README, "Onigmo is used as the default regexp library of Ruby 2.0 or later"; sources are C (`regcomp.c`, `regparse.c`). https://github.com/k-takata/Onigmo

### Rust

Does **not** use the `regex` crate (pure Rust). Uses `pcre2-sys`, low level bindings to the C PCRE2 library, wrapped in a hand written `mod pcre2`. Foreign C library. Because the image is Alpine (musl target), `pcre2-sys` statically links a PCRE2 copy it builds from source, per its README, even though `pcre2-dev` is installed (exact link mode on this build is **unverified**, not checked with `ldd`).

**Evidence**
- Install: [rust/regex-redux.yml:10](../../benchmarks/rust/regex-redux.yml) `apk add ... pcre2-dev pkgconf`; [rust/regex-redux/Cargo.toml](../../benchmarks/rust/regex-redux/Cargo.toml) `pcre2-sys = "0.2"`.
- Usage: [rust/regex-redux/main.rs:8](../../benchmarks/rust/regex-redux/main.rs) `extern crate pcre2_sys;`, [main.rs:19](../../benchmarks/rust/regex-redux/main.rs) `use pcre2_sys::*;`, [main.rs:94](../../benchmarks/rust/regex-redux/main.rs) `pcre2_compile_8(...)`.
- Engine language: pcre2-sys docs, "Low level bindings to PCRE2", https://docs.rs/pcre2-sys/latest/pcre2_sys/ ; README, "prefers dynamically linking with the host's PCRE2 system library", "Static linking will automatically happen for MUSL targets". https://github.com/BurntSushi/rust-pcre2/tree/master/pcre2-sys

### Swift

Uses Foundation's `NSRegularExpression` and `replacingOccurrences(of:options: .regularExpression)`. On Linux, swift-corelibs-foundation forwards to CoreFoundation's `_CFRegularExpression`, which calls ICU's `uregex` API. ICU is written in C/C++. No PCRE.

**Evidence**
- Install: none, [swift/regex-redux.yml:7](../../benchmarks/swift/regex-redux.yml) uses `swift:6.0.3`.
- Usage: [swift/regex-redux/main.swift:7](../../benchmarks/swift/regex-redux/main.swift) `import Foundation`, [main.swift:17](../../benchmarks/swift/regex-redux/main.swift) `NSRegularExpression(pattern: pattern, options: [])`, [main.swift:20-21](../../benchmarks/swift/regex-redux/main.swift) `replacingOccurrences(... options: .regularExpression)`.
- Engine language: `NSRegularExpression.swift` calls `_CFRegularExpressionCreate(...)`, https://github.com/swiftlang/swift-corelibs-foundation/blob/main/Sources/Foundation/NSRegularExpression.swift ; `CFRegularExpression.c` includes `<_foundation_unicode/uregex.h>` and calls `uregex_open(...)`, https://github.com/swiftlang/swift-corelibs-foundation/blob/main/Sources/CoreFoundation/CFRegularExpression.c

## Implications for the thesis

Nine languages (C, C++, C#, Haskell, Java, Lua, Python, Rust, plus Go on PCRE 1) delegate matching to the same family of C code, so their regex-redux results mostly measure PCRE plus the cost of each language's FFI, I/O and parallelism, not the language's own code generation. Erlang and PHP also run PCRE2, only bundled inside the runtime. The genuinely different engines are Irregexp (Node.js, Dart), Onigmo (Ruby), the Perl core engine, ICU (Swift), .NET Regex (F#) and the pure OCaml `re` library. Within .NET, C# and F# use different engines, so their regex-redux gap reflects the engine choice rather than the language.

## Open items

- C and C++: which Debian package in `gcc:15.2.0` provides `libpcre2-8.so` at link time.
- Rust: confirm static vs dynamic PCRE2 linkage of `/tmp/rust-regex-redux` with `ldd` inside the container.
- PHP: confirm with `php -i | grep -i pcre` inside `php:8.4-cli` that the bundled library is reported.

## Sources

- PCRE2 project: https://github.com/PCRE2Project/pcre2
- Erlang `re` docs: https://www.erlang.org/doc/apps/stdlib/re.html
- go-pcre README: https://github.com/GRbit/go-pcre
- pcre2-sys docs: https://docs.rs/pcre2-sys/latest/pcre2_sys/
- pcre2-sys README: https://github.com/BurntSushi/rust-pcre2/tree/master/pcre2-sys
- PHP PCRE installation: https://www.php.net/manual/en/pcre.installation.php
- docker-library php 8.4 cli Dockerfile: https://github.com/docker-library/php/blob/master/8.4/bookworm/cli/Dockerfile
- ocaml-re: https://github.com/ocaml/ocaml-re
- lrexlib: https://github.com/rrthomas/lrexlib
- V8 Irregexp: https://v8.dev/blog/non-backtracking-regexp
- V8 regexp source: https://github.com/v8/v8/tree/main/src/regexp
- Dart VM regexp: https://github.com/dart-lang/sdk/tree/main/runtime/vm/regexp
- .NET Regex source: https://github.com/dotnet/runtime/tree/main/src/libraries/System.Text.RegularExpressions/src/System/Text/RegularExpressions
- Onigmo: https://github.com/k-takata/Onigmo
- perlreguts: https://perldoc.perl.org/perlreguts
- swift-corelibs-foundation NSRegularExpression: https://github.com/swiftlang/swift-corelibs-foundation/blob/main/Sources/Foundation/NSRegularExpression.swift
- swift-corelibs-foundation CFRegularExpression: https://github.com/swiftlang/swift-corelibs-foundation/blob/main/Sources/CoreFoundation/CFRegularExpression.c
