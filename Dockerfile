FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    xz-utils \
    gnupg \
    build-essential \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Install Go and Node.js 
ENV GO_VERSION=1.25.2 \
    NODE_VERSION=24.10.0

RUN set -eux; \
    # Detect architecture
    ARCH=$(dpkg --print-architecture); \
    case "$ARCH" in \
        amd64) GO_ARCH=amd64; NODE_ARCH=x64 ;; \
        arm64) GO_ARCH=arm64; NODE_ARCH=arm64 ;; \
        *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac; \
    \
    # Install Go
    curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz" -o /tmp/go.tar.gz; \
    tar -C /usr/local -xzf /tmp/go.tar.gz; \
    rm /tmp/go.tar.gz; \
    \
    # Install Node.js
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz" -o /tmp/node.tar.xz; \
    tar -C /usr/local --strip-components 1 -xf /tmp/node.tar.xz; \
    rm /tmp/node.tar.xz

# Update PATH for Go
ENV PATH="/usr/local/go/bin:${PATH}"

# # Set the working directory inside the container
WORKDIR /app
COPY . .

RUN node ./src/langs/js/fib.js > /app/fib.log
