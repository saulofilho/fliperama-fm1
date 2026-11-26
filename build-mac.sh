#!/bin/sh
# FLIPERAMA: ./build.sh on a Mac, with the venv (Pillow, fontTools) and the AC79 SDK of ../fm1-rede/sdk.
# One-time setup: python3 -m venv .venv && .venv/bin/pip install Pillow fonttools
# The JieLi toolchain is ~/.jieli/toolchain; Docker Desktop must be running (the toolchain runs in linux/amd64).
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
PATH="$root/.venv/bin:$PATH" PYTHON="$root/.venv/bin/python" \
AC79_SDK="${AC79_SDK:-$root/../fm1-rede/sdk}" exec "$root/build.sh" "$@"
