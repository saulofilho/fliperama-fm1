#!/usr/bin/env python3
"""Publish offline review images from the exact 240x240 RGB565 host renderer."""
import argparse
from base64 import b64encode
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

FRAMES = (24, 25, 32, 40)
HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("output", type=Path)
    ap.add_argument("catalog", type=Path)
    args = ap.parse_args()
    out = args.output
    raw = out / "frames"
    scenes = json.loads((HERE / "world-scenes.json").read_text())
    catalog = [e for e in json.loads(args.catalog.read_text())["engines"] if e["name"] != "EMPTY"]
    knobs = {}
    for line in (out / "knobs.tsv").read_text().splitlines():
        e, _, lo, hi, label = line.split("\t")
        knobs[int(e)] = dict(min=int(lo), max=int(hi), label=label)
    assert len(scenes) == len(catalog) == len(knobs) == 30

    def img(theme, engine, mode, f):
        with Image.open(raw / f"{theme}-{engine:02d}-{mode}-{f:02d}.ppm") as im:
            assert im.size == (240, 240)
            return im.convert("RGB")

    def atlas(theme, engine, mode, n):
        im = Image.new("RGB", (1920, ((n + 7) // 8) * 240))
        for f in range(n):
            im.paste(img(theme, engine, mode, f), (f % 8 * 240, f // 8 * 240))
        with BytesIO() as data:
            im.save(data, "WEBP", lossless=True, method=0)
            return b64encode(data.getvalue()).decode("ascii")

    worlds = []
    for e in catalog:
        eid = e["id"]
        title, summary, *reactions = scenes[str(eid)]
        for theme in range(2):
            # Exclude the knobs, values and transport from the visual check.
            for mode, a, b in [(1, 0, 24), (2, 8, 16), (3, 3, 8)]:
                before = img(theme, eid, mode, a).crop((16, 98, 224, 189))
                after = img(theme, eid, mode, b).crop((16, 98, 224, 189))
                assert ImageChops.difference(before, after).getbbox(), (theme, eid, mode)
        worlds.append(dict(**e, title=title, summary=summary, reactions=reactions, knob=knobs[eid],
                           frames=FRAMES, atlases=[[atlas(theme, eid, m, n) for m, n in enumerate(FRAMES)] for theme in range(2)]))
    print("30 engines × 2 themes × 121 frames: 7,260 native frames; knob / chord / rhythm pixel changes checked")

    def board(panels, mode, f):
        w = 16 + len(panels) * 256
        im = Image.new("RGB", (w, 300), "#181b15")
        d = ImageDraw.Draw(im)
        d.text((16, 10), "JAZZY    /    A LITTLE WORLD OF SOUND    /    240 x 240 LCD", fill="#e4e97e")
        for i, (theme, eid, name) in enumerate(panels):
            x = 16 + i * 256
            im.paste(img(theme, eid, mode, f), (x, 31))
            d.text((x, 278), name, fill="#efefe3")
        return im

    panels = [(0, 16, "ACID / DARK"), (1, 16, "ACID / LIGHT"), (0, 19, "SWAV-SAW / DARK"), (1, 15, "BREAK / LIGHT")]
    frames = [board(panels, 3, f) for f in range(FRAMES[3])]
    frames[2].save(out / "JAZZY-Motion-Study.png")
    frames[0].save(out / "JAZZY-Motion-Study.gif", save_all=True, append_images=frames[1:], duration=50, loop=0)
    sheet = Image.new("RGB", (1280, 812), "#181b15")
    d = ImageDraw.Draw(sheet)
    d.text((16, 10), "JAZZY    /    MOTION STUDY    /    30 ENGINES", fill="#e4e97e")
    for i, e in enumerate(catalog):
        x, y = 16 + (i % 5) * 252, 28 + (i // 5) * 128
        sheet.paste(img(0, e["id"], 3, 2).crop((0, 78, 240, 188)), (x, y))
        d.text((x+6,y+111), f"{i+1:02d}  {e['name']}", fill="#efefe3")
    sheet.save(out / "JAZZY-30-Engines.png")
    def utility(theme, f):
        im = Image.new("RGB", (1024, 562), "#181b15")
        d = ImageDraw.Draw(im)
        d.text((16, 10), "JAZZY    /    WORKSTATION    /    " + ("LIGHT" if theme else "DARK"), fill="#e4e97e")
        for k, name in enumerate(("MIXER", "SEQUENCER", "DELAY", "REVERB", "PHASER", "SENDS", "SCREEN SETTINGS")):
            x, y = 16 + (k % 4) * 252, 30 + (k // 4) * 264
            im.paste(img(theme, 90 + k, 3, f), (x, y))
            d.text((x, y + 245), name, fill="#efefe3")
        return im

    utility_urls = []
    for theme, label in enumerate(("DARK", "LIGHT")):
        util = [utility(theme, f) for f in range(24)]
        path = out / f"JAZZY-Workstation-{label}.gif"
        util[0].save(path, save_all=True, append_images=util[1:], duration=80, loop=0)
        utility_urls.append("data:image/gif;base64," + b64encode(path.read_bytes()).decode("ascii"))
    html = (HERE / "world-preview.html").read_text().replace("/* DATA */[]", json.dumps(worlds, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/* UTILITY */[]", json.dumps(utility_urls))
    (out / "JAZZY-Motion-Study.html").write_text(html)
    guide = [
        "# JAZZY — A Little World of Sound",
        "",
        "FM-1 240×240 LCD motion study. DARK and LIGHT share the same layout.",
        "The clips simulate knob, note and rhythm input. They are silent and use the firmware's C UI renderer.",
        "",
        "| Engine | Scene | Knob | Chord | Rhythm |",
        "|---|---|---|---|---|",
    ]
    for w in worlds:
        a,b,c = w["reactions"]
        guide.append(f"| {w['name']} | {w['title']} | {w['knob']['label']}: {a} | {b} | {c} |")
    guide.extend(["", "Visual references: [OP-1 field](https://teenage.engineering/guides/op-1#punch), [OP-XY](https://teenage.engineering/guides/op-xy/synth-engines)."])
    (out / "JAZZY-Scene-Map.md").write_text("\n".join(guide) + "\n")


if __name__ == "__main__":
    main()
