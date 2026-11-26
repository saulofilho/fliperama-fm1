#!/bin/sh
# Local Mac setup; dependencies live on the external SSD. No device writes.
set -eu
cd "$(dirname "$0")/../.."
export PATH="/Volumes/SSD/Development/Toolchains/fm1-six-tooling/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export JIELI_NERDCTL=1
export JIELI_TOOLCHAIN=/Volumes/SSD/Development/Toolchains/fm1-six-tooling/jieli/toolchain
export AC79_SDK=/Volumes/SSD/Development/Toolchains/fm1-six-tooling/fw-AC79_AIoT_SDK
exec /Volumes/SSD/Development/Toolchains/fm1-six-tooling/python/bin/python3 tools/six/build.py "$@"
