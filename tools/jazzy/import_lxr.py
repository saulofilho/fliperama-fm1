#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Project pinned Elixir factory voices onto the JAZZY one-shot engine."""
import argparse
import hashlib
import math
import struct
from collections import Counter
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "d35a1cc45248e2c3d68014aaa1d3a34d6787a6f4"
KITS = (1, 2, 3, 4, 20, 32)
ROLES = ("D1", "D2", "D3", "SN", "CY", "CH", "OH")


def bounded(value, lo=0, hi=127):
    return min(hi, max(lo, round(value)))


def decay(value, slope):
    # Elixir's slope EG, expressed as the time to reach 1/e.
    v = value / 127
    step = min(1, 2 * (1 - 1999 * v / (1 + 1998 * v)))
    a = (slope / 127 - .5) * 1.999
    k = 2 * a / (1 - a)
    y = math.exp(-1)
    level = y / (1 + k * (1 - y))
    ms = max(3, (1 - level) * 64000 / 44100 / max(step, 1e-9))
    return bounded(127 * math.log(max(1, 6.9 * ms / 5), 800))


def voice(data, kind, numbers):
    p = lambda name: data[numbers[name]]
    index = min(kind, 5)
    n = index + 1
    note = p(f"COARSE{n}")
    fine = bounded((p(f"FINE{n}") / 127 - .5) * 16, -8, 8)
    attack = p(f"VELOA{n}")
    dec = p(f"VELOD{n}" if kind < 5 else f"VELOD6_{'OPEN' if kind == 6 else 'CLOSED'}")
    dec = decay(dec, p(f"VOL_SLOPE{n}"))
    sweep = bounded(24 * math.log2(1 + 32 * (p(f"MODAMNT{n}") / 127) ** 2), 0, 126) if kind < 4 else 0
    sweep_time = p(f"MOD_EG{n}") if kind < 4 else 0
    mix = 0
    sub2 = wave2 = amount2 = 0
    if kind < 3:
        wave, modwave = p(f"OSC_WAVE_DRUM{n}"), p(f"MOD_WAVE_DRUM{n}")
        sub, amount = p(f"FM_FREQ{n}"), p(f"FMAMNT{n}")
        mix = bool(p(f"MIX_MOD_{n}"))
    elif kind == 3:
        wave, modwave = p("OSC_WAVE_SNARE"), 4
        sub, amount = p("NOISE_FREQ1"), p("MIX1")
    else:
        prefix, suffix = ("CYM", "_CYM") if kind == 4 else ("HH", "")
        wave, modwave, wave2 = (p(f"WAVE{i}_{prefix}") for i in range(1, 4))
        sub, sub2 = (p(f"MOD_OSC_F{i}{suffix}") for i in range(1, 3))
        amount, amount2 = (p(f"MOD_OSC_GAIN{i}{suffix}") for i in range(1, 3))
    cut = p(f"FILTER_FREQ_{n}") / 127
    hz = 44100 * .45 * (.1 * cut / (1 - .9 * cut))
    cutoff = bounded(127 * math.log(max(hz, 30) / 30) / math.log(16000 / 30))
    return (note, fine, wave | modwave << 3 | mix << 6, wave2, sub, sub2, amount, amount2,
            attack, dec, sweep, sweep_time, cutoff, p(f"RESO_{n}"), p(f"FILTER_TYPE_{n}"),
            p(f"TRANS{n}_VOL"), p(f"TRANS{n}_WAVE"), p(f"DRIVE{n}" if kind < 3 else
            ("SNARE", "CYMBAL", "HAT")[index - 3] + "_DISTORTION"),
            p(f"VOICE_DECIMATION{n}"), p(f"VOL{n}"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("elixir", type=Path)
    ap.add_argument("--reference", type=Path, help="write projected rows in preset order for host verification")
    args = ap.parse_args()
    numbers = dict((name, int(value)) for name, value in re.findall(
        r"\bPAR_(\w+)\s*=\s*(\d+)", (args.elixir / "firmware/src/lxr_params.h").read_text()))
    paths = {int(p.name[:3]): p for p in (args.elixir / "assets/kits/factory").glob("*.SND")}
    if len(paths) != 85 or set(paths) != set(range(1, 86)):
        raise SystemExit("Unexpected Elixir factory inventory")
    order = list(KITS) + [n for n in sorted(paths) if n not in KITS]
    labels, rows, notes = [], [[] for _ in ROLES], []
    for number in order:
        source = paths[number]
        raw = source.read_bytes()
        if len(raw) != 255:
            raise SystemExit(f"Unexpected LXR file size: {source}")
        label = source.stem[4:].replace("_", "-")
        labels.append(label.encode("ascii").ljust(8, b"\0"))
        notes.append(f" * {source.name} SHA256 {hashlib.sha256(raw).hexdigest()}")
        for kind in range(len(ROLES)):
            rows[kind].append(voice(raw[8:], kind, numbers))

    data = bytearray(b"".join(labels))
    group_starts = []
    for patches in rows:
        unique = list(dict.fromkeys(patches))
        ids = {p: i for i, p in enumerate(unique)}
        group_starts.append(len(data))
        data.extend(ids[p] for p in patches)
        columns = []
        for col in zip(*unique):
            low = min(col)
            width = (max(col) - low).bit_length()
            count = Counter(col)
            choices = [(len(col) * width, 0, [])]
            for bits in range(1, min(width, 5)):
                if len(count) <= (1 << bits) - 1:
                    continue
                top = [value for value, _ in count.most_common((1 << bits) - 1)]
                misses = len(col) - sum(count[value] for value in top)
                choices.append((len(col) * bits + misses * width + len(top) * 8, bits, top))
            _, bits, top = min(choices)
            columns.append((low, width, bits, top))
            data.extend((low & 255, width | bits << 4))
            data.extend(v & 255 for v in top)
        table = len(data)
        data.extend(bytes(2 * ((len(unique) + 7) // 8)))
        for base in range(0, len(unique), 8):
            struct.pack_into("<H", data, table + base // 4, len(data))
            word = size = 0
            for patch in unique[base:base + 8]:
                for value, (low, width, bits, top) in zip(patch, columns):
                    if bits:
                        code = top.index(value) if value in top else (1 << bits) - 1
                        word |= code << size
                        size += bits
                        if code < len(top):
                            continue
                    word |= (value - low) << size
                    size += width
            data.extend(word.to_bytes((size + 7) // 8, "little"))
    if args.reference:
        args.reference.write_bytes(bytes(v & 255 for kit in range(len(order))
            for kind in range(len(ROLES)) for v in rows[kind][kit]))
    root = ROOT / "rhythmer/firmware/jazzy"
    (root / "lxr_factory.h").write_text(
        f"/* Generated by tools/jazzy/import_lxr.py from Elixir {COMMIT}.\n"
        " * LXR factory data by Erica Synths / Hrtl. See LICENSING.md.\n"
        + "\n".join(notes) + "\n */\n#pragma once\n"
        f"#define LXR_KITS {len(order)}u\n#define LXR_DATA_BYTES {len(data)}u\n"
        "static const uint16_t LXR_GROUP[] = {" + ",".join(map(str, group_starts)) + "};\n"
        "static const uint8_t LXR_SOURCE[] = {\n"
        + "".join("    " + ",".join(map(str, data[k:k+24])) + ",\n" for k in range(0, len(data), 24))
        + "};\n")
    print(f"{len(order)} factory sets, {7 * len(order)} voices, {len(data)} bytes")


if __name__ == "__main__":
    main()
