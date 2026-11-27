"""FLIPERAMA's icon: a 16x16 pixel joystick. Writes site/icon.svg, site/favicon-32.png, site/apple-touch-icon.png
(180x180) and site/favicon.ico. Needs Pillow (the build's .venv has it): .venv/bin/python tools/share/icon.py"""
from pathlib import Path
from PIL import Image

ROWS = ["................",
        "......mmmm......",
        ".....mmmmmm.....",
        "....mmppmmmm....",
        "....mpppmmmm....",
        "....mmpmmmmd....",
        ".....mmmmmd.....",
        "......mddd......",
        ".......cc.......",
        ".......cc.......",
        ".......cc.......",
        "...vvvvvvvvvv...",
        "..vVVVyVVVrVVv..",
        "..vvvvvvvvvvvv..",
        "..dddddddddddd..",
        "................"]
BG = "#120A2A"
C = {"m": "#E04FD0", "p": "#F6A8E4", "d": "#8E3BD8", "c": "#F3E6C8", "v": "#8E3BD8", "V": "#B9A3F5",
     "y": "#F2C14E", "r": "#7FE7F2"}
site = Path(__file__).resolve().parents[2] / "site"

svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" shape-rendering="crispEdges">',
       f'<rect width="16" height="16" rx="3" fill="{BG}"/>']
for y, row in enumerate(ROWS):
    x = 0
    while x < 16:
        ch = row[x]
        if ch == ".":
            x += 1
            continue
        w = 1
        while x + w < 16 and row[x + w] == ch:
            w += 1
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="1" fill="{C[ch]}"/>')
        x += w
svg.append("</svg>")
(site / "icon.svg").write_text("\n".join(svg) + "\n")

img = Image.new("RGB", (16, 16), BG)
for y, row in enumerate(ROWS):
    for x, ch in enumerate(row):
        if ch != ".":
            img.putpixel((x, y), Image.new("RGB", (1, 1), C[ch]).getpixel((0, 0)))
img.resize((32, 32), Image.NEAREST).save(site / "favicon-32.png")
big = Image.new("RGB", (180, 180), BG)
big.paste(img.resize((160, 160), Image.NEAREST), (10, 10))
big.save(site / "apple-touch-icon.png")
img.resize((48, 48), Image.NEAREST).save(site / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
print("icon: icon.svg favicon-32.png apple-touch-icon.png favicon.ico")
