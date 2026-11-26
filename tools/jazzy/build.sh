#!/bin/sh
set -eu
mount | grep -q ' on /Volumes/SSD ' || { echo 'SSD not mounted' >&2; exit 1; }
ROOT=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
export RHYTHMER_BUILD_DIR=${RHYTHMER_BUILD_DIR:-/Volumes/SSD/Development/BuildCache/jazzy}
export JAZZY_EXTERNAL_ASSETS=${JAZZY_EXTERNAL_ASSETS:-1}
export JAZZY_OPT=${JAZZY_OPT:--Oz}
export TMPDIR=/Volumes/SSD/Development/Caches/jazzy/tmp
export PYTHONPYCACHEPREFIX=/Volumes/SSD/Development/Caches/jazzy/python
mkdir -p "$TMPDIR" "$RHYTHMER_BUILD_DIR/source"
/Volumes/SSD/Development/Toolchains/fm1-six-tooling/python/bin/python3 "$ROOT/tools/jazzy/pack_synth_assets.py"
export PATH="/Volumes/SSD/Development/Toolchains/fm1-six-tooling/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export JIELI_NERDCTL=1
export JIELI_GUEST_TOOLCHAIN=/Volumes/SSD/fm1-six-tooling/jieli/toolchain
export JIELI_TOOLCHAIN=/Volumes/SSD/Development/Toolchains/fm1-six-tooling/jieli/toolchain
export RHYTHMER_EMBEDDED_BANKS=/Volumes/SSD/Development/BuildCache/jazzy/synth-banks
if [ "$JAZZY_EXTERNAL_ASSETS" = 1 ]; then
    /Volumes/SSD/Development/Toolchains/fm1-six-tooling/python/bin/python3 "$ROOT/tools/jazzy/pack_catalog.py" "$RHYTHMER_EMBEDDED_BANKS"
fi
export AC79_SDK=/Volumes/SSD/Development/Toolchains/fm1-six-tooling/fw-AC79_AIoT_SDK
rsync -a --exclude build --exclude build-ssd "$ROOT/rhythmer/" "$RHYTHMER_BUILD_DIR/source/"
exec /Volumes/SSD/Development/Toolchains/fm1-six-tooling/python/bin/python3 "$RHYTHMER_BUILD_DIR/source/tools/build.py" "$@"
