#!/usr/bin/env python3
"""Encode the frames from jazzy_world_preview --gallery for the JAZZY site."""
import argparse
from pathlib import Path

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames", type=Path)
    parser.add_argument("assets", type=Path)
    args = parser.parse_args()

    engine_ids = [
        int(line.split("\t", 1)[0])
        for line in (args.frames / "knobs.tsv").read_text().splitlines()
    ]
    for engine in engine_ids:
        stem = f"engine-{engine:02d}"
        mode = 2 if engine in (26, 41) else 3
        files = sorted(args.frames.glob(f"0-{engine:02d}-{mode}-*.ppm"))
        if len(files) not in (32, 40):
            raise ValueError(f"{stem}: expected one chord or rhythm sequence")
        images = []
        for file in files:
            with Image.open(file) as frame:
                if frame.size != (240, 240):
                    raise ValueError(f"{file}: expected a native 240×240 frame")
                images.append(frame.convert("RGB"))
        if len({frame.crop((16, 98, 224, 189)).tobytes() for frame in images}) < 6:
            raise ValueError(f"{stem}: too little motion inside the scene")

        images[12].save(args.assets / f"{stem}.png", optimize=True)
        images[0].save(args.assets / f"{stem}.webp", save_all=True,
                       append_images=images[1:], lossless=True,
                       duration=50, loop=0)
    print(f"Encoded {len(engine_ids)} native engine animations")


if __name__ == "__main__":
    main()
