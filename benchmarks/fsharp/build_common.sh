#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <benchmark-name>" >&2
  exit 1
fi

BENCH="$1"
case "$BENCH" in
  binary-trees|fannkuch-redux|fasta|k-nucleotide|mandelbrot|n-body|regex-redux|spectral-norm)
    ;;
  *)
    echo "[ERROR] Unsupported benchmark '$BENCH'" >&2
    exit 2
    ;;
esac

if ! command -v dotnet >/dev/null 2>&1; then
  echo "[ERROR] Command not found 'dotnet'" >&2
  exit 127
fi

OS="$(uname -s)"
ARCH="$(uname -m)"
RID="linux-x64"

# Keep linux-x64 as default; only fall back when host is not Linux x86_64/amd64.
if [ "$OS" != "Linux" ] || { [ "$ARCH" != "x86_64" ] && [ "$ARCH" != "amd64" ]; }; then
  RID="linux-arm64"
fi

SRC_FS="/tmp/repo/benchmarks/fsharp/$BENCH/main.fs"
BUILD_DIR="/tmp/fsharp-build/$BENCH"
PROJECT_FILE="$BUILD_DIR/program.fsproj"
OUT_BIN="/tmp/fsharp-$BENCH"

if [ ! -f "$SRC_FS" ]; then
  echo "[ERROR] Missing source file '$SRC_FS'" >&2
  exit 3
fi

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cp "$SRC_FS" "$BUILD_DIR/Program.fs"

{
  cat <<EOF
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <RuntimeIdentifier>$RID</RuntimeIdentifier>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
    <ServerGarbageCollection>true</ServerGarbageCollection>
    <ConcurrentGarbageCollection>true</ConcurrentGarbageCollection>
    <PublishAot>false</PublishAot>
  </PropertyGroup>
EOF

  if [ "$BENCH" = "k-nucleotide" ]; then
    cat <<'EOF'
  <ItemGroup>
    <PackageReference Include="Microsoft.Experimental.Collections" Version="1.0.6-e190117-3" />
  </ItemGroup>
EOF
  fi

  cat <<'EOF'
  <ItemGroup>
    <Compile Include="Program.fs" />
  </ItemGroup>
</Project>
EOF
} > "$PROJECT_FILE"

DOTNET_CLI_TELEMETRY_OPTOUT=1 \
DOTNET_NOLOGO=1 \
NUGET_PACKAGES=/tmp/nuget-packages \
dotnet build -r "$RID" -c Release "$PROJECT_FILE"

BIN="$BUILD_DIR/bin/Release/net9.0/$RID/program"

if [ ! -f "$BIN" ]; then
  echo "[ERROR] Build output not found '$BIN'" >&2
  exit 4
fi

cp "$BIN" "$OUT_BIN"
chmod +x "$OUT_BIN"
