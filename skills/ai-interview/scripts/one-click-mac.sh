#!/bin/bash
# No curl|sh or sudo. Starts the local, source-auditable Python installer.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "AI Interview one-click setup supports macOS; use README manual setup on this OS." >&2
  exit 2
fi
PY=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; exit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then
    PY="$(command -v "$candidate")"
    break
  fi
done
if [[ -z "$PY" ]]; then
  # A dry run must never install even a Python interpreter.
  for arg in "$@"; do
    if [[ "$arg" == "--dry-run" || "$arg" == "--doctor" ]]; then
      echo 'Python 3.10+ is missing. Install Python 3.11 (or uv/Homebrew), then rerun.'
      echo 'No dependency, model or application was installed.'
      exit 0
    fi
  done
  AUTO_APPROVED=false
  for arg in "$@"; do
    if [[ "$arg" == "--yes" ]]; then AUTO_APPROVED=true; fi
  done
  if [[ "$AUTO_APPROVED" == false ]]; then
    if [[ ! -t 0 ]]; then
      echo 'Python installation requires explicit --yes in a noninteractive Agent session.' >&2
      exit 2
    fi
    read -r -p 'Install Python 3.11 via existing uv/Homebrew? [y/N]: ' choice
    if [[ "$choice" != "y" && "$choice" != "Y" && "$choice" != "yes" ]]; then
      echo 'Python installation declined.' >&2
      exit 2
    fi
  fi
  if command -v uv >/dev/null 2>&1; then
    echo 'Using existing uv to prepare a Python 3.11 interpreter.'
    uv python install 3.11
    PY="$(uv python find 3.11)"
  elif command -v brew >/dev/null 2>&1; then
    echo 'Using existing Homebrew to install Python 3.11.'
    brew install python@3.11
    PY="$(brew --prefix python@3.11)/bin/python3.11"
  else
    # Clean Apple Silicon Macs may have only Python 3.9. Use an official pinned
    # uv binary with a pinned upstream GitHub SHA256, never curl|sh or sudo.
    UV_VERSION='0.13.1'
    case "$(uname -m)" in
      arm64)
        UV_ARCH='aarch64-apple-darwin'
        UV_SHA='cfe454573412ff7380d15fc7dae5997ab53ffce72fce0a78e91ddbc84001acd2'
        ;;
      x86_64)
        UV_ARCH='x86_64-apple-darwin'
        UV_SHA='bb7b805bdcf3d0bc8c74ceb94569e6b3e8aa35bd492acdbb9d46bf46d9d4ff6b'
        ;;
      *) echo 'Unknown CPU architecture; cannot select a verified uv binary.' >&2; exit 2;;
    esac
    TEMP_UV="$(mktemp -d "${TMPDIR:-/tmp}/ai-interview-uv.XXXXXX")"
    trap 'rm -rf -- "$TEMP_UV"' EXIT
    URL="https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-${UV_ARCH}.tar.gz"
    echo "Downloading the verified official uv ${UV_VERSION} binary (temporary, no system installation)."
    curl --fail --location --proto '=https' --proto-redir '=https' --tlsv1.2 \
      --max-filesize 30000000 --connect-timeout 20 --max-time 240 \
      --output "$TEMP_UV/uv.tar.gz" "$URL"
    ACTUAL_SHA="$(shasum -a 256 "$TEMP_UV/uv.tar.gz" | awk '{print $1}')"
    if [[ "$ACTUAL_SHA" != "$UV_SHA" ]]; then
      echo 'Official uv archive SHA256 verification failed; refusing to execute.' >&2
      exit 2
    fi
    tar -xzf "$TEMP_UV/uv.tar.gz" -C "$TEMP_UV"
    UV_BIN="$TEMP_UV/uv-${UV_ARCH}/uv"
    if [[ ! -f "$UV_BIN" ]]; then
      echo 'Verified uv archive does not contain the expected binary.' >&2
      exit 2
    fi
    "$UV_BIN" python install 3.11
    PY="$("$UV_BIN" python find 3.11)"
  fi
fi
exec "$PY" "$HERE/mac_bootstrap.py" "$@"
