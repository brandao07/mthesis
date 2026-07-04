# Setup & Uninstall

> Part of the [main README](../README.md). Linux-only (Ubuntu 22.04 / 24.04).

## Linux Setup (Ubuntu 22.04/24.04)

Use `make setup` to bootstrap the full local environment (Linux only):

```bash
make setup
```

`make setup`:

- checks/install required base tools (`git`, `curl`, `make`, `gcc`, etc.)
- installs Docker if missing and enables the daemon
- installs/ensures Python `3.12`
- installs/ensures the Go version required by `kwa/go.mod`
- clones GMT into this repo at `./green-metrics-tool`
- runs GMT `install_linux.sh` non-interactively with local URLs
- attempts full metric-provider dependency setup, retrying with best-effort fallbacks for hardware-specific providers if needed
- generates the benchmark input files (`inputs/fasta-*.txt`) via `scripts/generate_inputs.sh`

Important notes:

- This setup is intended for Ubuntu `22.04` and `24.04` only.
- `sudo` is required.
- If your user is newly added to the `docker` group, you may need to relogin (or run `newgrp docker`) before running Docker without sudo.
- If `./green-metrics-tool` already exists, setup prompts whether to overwrite it.
- DB defaults are sourced from `kwa/.env.example` (notably `DATABASE_PASSWORD`).

## Uninstall

Use `make uninstall` for safe local teardown:

```bash
make uninstall
```

`make uninstall`:

- always asks whether to remove DB/data volume
- stops/removes GMT containers (best effort)
- runs `docker system prune` (best effort)
- removes local artifacts:
  - `kwa/build`
  - `.gocache`
  - `.gocache_local`
  - `.gomodcache`
  - `./green-metrics-tool`
- prompts (Linux) whether to remove pre-install requirements and Docker packages

Notes:

- This uninstall flow is Linux-oriented and destructive.
- `sudo` may be required for package/sudoers cleanup.
