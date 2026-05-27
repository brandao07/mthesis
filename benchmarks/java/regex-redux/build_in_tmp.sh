#!/bin/sh
set -eu

WORKDIR="/tmp/java-build/regex-redux"
JEXTRACT_VERSION="22"
JEXTRACT_BUILD="6-47"
JEXTRACT_DIR="/tmp/jextract-${JEXTRACT_VERSION}"

# Detect architecture for jextract download.
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) JEXTRACT_ARCH="linux-x64" ;;
  aarch64|arm64) JEXTRACT_ARCH="linux-aarch64" ;;
  *) echo "[ERROR] Unsupported architecture: $ARCH" >&2; exit 1 ;;
esac

JEXTRACT_TAR="openjdk-${JEXTRACT_VERSION}-jextract+${JEXTRACT_BUILD}_${JEXTRACT_ARCH}_bin.tar.gz"
JEXTRACT_URL="https://download.java.net/java/early_access/jextract/${JEXTRACT_VERSION}/${JEXTRACT_BUILD%%-*}/${JEXTRACT_TAR}"

# Install PCRE2 development headers required by jextract to generate bindings.
if command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get install -y --no-install-recommends libpcre2-dev && rm -rf /var/lib/apt/lists/*
elif command -v microdnf >/dev/null 2>&1; then
    microdnf install -y pcre2-devel
elif command -v dnf >/dev/null 2>&1; then
    dnf install -y pcre2-devel
else
    echo "[ERROR] No supported package manager found (apt-get/microdnf/dnf)" >&2; exit 1
fi

# Download and extract jextract if not already present.
if [ ! -x "${JEXTRACT_DIR}/bin/jextract" ]; then
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL -o /tmp/jextract.tar.gz "$JEXTRACT_URL"
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O /tmp/jextract.tar.gz "$JEXTRACT_URL"
    else
        echo "[ERROR] Neither curl nor wget available to download jextract" >&2; exit 1
    fi
    tar -xzf /tmp/jextract.tar.gz -C /tmp/
    rm /tmp/jextract.tar.gz
fi

mkdir -p "$WORKDIR/Include/java"

# Generate PCRE2 Java bindings using jextract (matches CLBG build command).
"${JEXTRACT_DIR}/bin/jextract" \
    -D "PCRE2_CODE_UNIT_WIDTH=8" \
    -l pcre2-8 \
    /usr/include/pcre2.h \
    -t jextract_pcre2 \
    --source \
    --output "$WORKDIR/Include/java"

# Copy source with the correct filename to match the public class declaration.
cp /tmp/repo/benchmarks/java/regex-redux/Main.java "$WORKDIR"/regexredux.java

cd "$WORKDIR"
javac -d . -cp . --source-path Include/java regexredux.java

# Prefer G1 when available (as in Oracle GraalVM builds), fall back to serial.
if ! native-image --silent --gc=G1 \
    -H:+UnlockExperimentalVMOptions \
    -H:+ForeignAPISupport \
    --enable-native-access=ALL-UNNAMED \
    --features=ForeignRegistrationFeature \
    -Djava.library.path=Include/java/jextract_pcre2 \
    -cp . -O3 -march=native regexredux \
    -o regexredux.graalvmaot-4.graalvmaot_run; then
  native-image --silent --gc=serial \
    -H:+UnlockExperimentalVMOptions \
    -H:+ForeignAPISupport \
    --enable-native-access=ALL-UNNAMED \
    --features=ForeignRegistrationFeature \
    -Djava.library.path=Include/java/jextract_pcre2 \
    -cp . -O3 -march=native regexredux \
    -o regexredux.graalvmaot-4.graalvmaot_run
fi
