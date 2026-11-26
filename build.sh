#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
python=${PYTHON:-python3}
export JIELI_TOOLCHAIN=${JIELI_TOOLCHAIN:-"$HOME/.jieli/toolchain"}
export AC79_SDK=${AC79_SDK:-"$HOME/fw-AC79_AIoT_SDK"}
export RHYTHMER_BUILD_DIR=${RHYTHMER_BUILD_DIR:-"$root/build"}
mkdir -p "$RHYTHMER_BUILD_DIR/gen"
RHYTHMER_BUILD_DIR=$(CDPATH= cd -- "$RHYTHMER_BUILD_DIR" && pwd)
export JAZZY_EXTERNAL_ASSETS=1 JAZZY_OPT=-Oz
export JAZZY_FACTORY_BANKS=${JAZZY_FACTORY_BANKS:-"$root/factory-banks"}
export JAZZY_ASSET_BANK_DIR="$RHYTHMER_BUILD_DIR/synth-banks"
export RHYTHMER_EMBEDDED_BANKS="$JAZZY_ASSET_BANK_DIR"
cp "$root/generated/"* "$RHYTHMER_BUILD_DIR/gen/"
"$python" "$root/tools/jazzy/pack_synth_assets.py"
"$python" "$root/tools/jazzy/pack_catalog.py" "$JAZZY_ASSET_BANK_DIR"
exec "$python" "$root/rhythmer/tools/build.py" --reuse-generated --product FM-1_900 "$@"
