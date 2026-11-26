#!/bin/sh
set -eu
mount | grep -q ' on /Volumes/SSD ' || exit 1
ROOT=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
BUILD=/Volumes/SSD/Development/BuildCache/jazzy
export PYTHONPYCACHEPREFIX=/Volumes/SSD/Development/Caches/jazzy/python
export TMPDIR=/Volumes/SSD/Development/Caches/jazzy/tmp
for test in jazzy_integration_test jazzy_audio_test jazzy_priority_test jazzy_factory_test jazzy_mix_test jazzy_editor_test jazzy_lxr_save_test jazzy_usb_host_ui_test jazzy_duck_test; do
 clang -w -O1 -fwrapv -DJUNGLE_AUDIO_CODE= -fsanitize=address,undefined -I"$BUILD/gen" -I"$ROOT/rhythmer/firmware/src" "$ROOT/rhythmer/tests/$test.c" "$ROOT/rhythmer/firmware/six/jungle.c" "$ROOT/rhythmer/firmware/six/tb3po.c" "$ROOT/rhythmer/firmware/six/acid_generate.c" -lm -o "$BUILD/$test"
 "$BUILD/$test"
done

clang -w -O1 -fwrapv -DJUNGLE_AUDIO_CODE= -fsanitize=address,undefined -I"$BUILD/gen" -I"$ROOT/rhythmer/firmware/src" "$ROOT/rhythmer/tests/jazzy_expansion_test.c" "$ROOT/rhythmer/firmware/six/jungle.c" "$ROOT/rhythmer/firmware/six/tb3po.c" "$ROOT/rhythmer/firmware/six/acid_generate.c" -lm -o "$BUILD/jazzy_expansion_test"
"$BUILD/jazzy_expansion_test" "$BUILD/synth-banks/amen-160.slot" "$BUILD/synth-banks/think-160.slot" "$BUILD/synth-banks/da000.bin" "$BUILD/synth-banks/94000.bin" "$BUILD/synth-banks/95000.bin" "$BUILD/gen/ui_font_tail.bin" "$BUILD/synth-banks/93020.bin"
clang -w -O1 -DJAZZY_EXTERNAL_ASSETS=1 -fsanitize=address,undefined "$ROOT/rhythmer/tests/six_upload_test.c" -o "$BUILD/jazzy_upload_test"
"$BUILD/jazzy_upload_test" "$BUILD/synth-banks/amen-160.slot"

for ota in 0 1; do
 clang -w -O1 -g -fwrapv -DFELUCCA_OTA="$ota" -fsanitize=address,undefined "$ROOT/rhythmer/tests/usb_host_test.c" -o "$BUILD/jazzy_usb_host_bus_$ota"
 "$BUILD/jazzy_usb_host_bus_$ota"
done
