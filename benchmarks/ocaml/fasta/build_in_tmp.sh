#!/bin/sh
set -eu

SRC_ML="/tmp/ocaml-fasta.ml"
BIN="/tmp/ocaml-fasta"

cp /tmp/repo/benchmarks/ocaml/fasta/main.ml "$SRC_ML"

opam exec -- ocamlopt \
  -noassert \
  -unsafe \
  -fPIC \
  -nodynlink \
  -inline 100 \
  -O3 \
  -I +unix unix.cmxa \
  -ccopt -march=native \
  "$SRC_ML" \
  -o "$BIN"

rm -f "$SRC_ML" /tmp/ocaml-fasta.cmi /tmp/ocaml-fasta.cmx /tmp/ocaml-fasta.o
