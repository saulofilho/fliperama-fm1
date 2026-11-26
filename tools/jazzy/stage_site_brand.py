#!/usr/bin/env python3
"""Apply dual firmware navigation and native startup motion to the local preview."""
from pathlib import Path
import re
import shutil

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
PREVIEW = ROOT / 'qa/site-preview'
BUILD = Path('/Volumes/SSD/Development/BuildCache')
RHYTHMER = PREVIEW / 'rhythmer'


def write_boot(frames, output):
    images = []
    for frame in sorted(frames):
        with Image.open(frame) as image:
            images.append(image.convert('RGB'))
    assert len(images) == 27 and all(img.size == (240, 240) for img in images)
    assert len({img.tobytes() for img in images}) > 12
    images[19].save(output.with_suffix('.png'), optimize=True)
    images[0].save(output.with_suffix('.webp'), save_all=True, append_images=images[1:],
                   duration=[80] * 26 + [30_000], loop=0, lossless=True)


def update_rhythmer_navigation():
    for file in RHYTHMER.rglob('*.html'):
        root = '../' * len(file.parent.relative_to(RHYTHMER).parts)
        page = file.read_text()
        if 'data-rhythmer-navigation' not in page and '<header class="topbar">' not in page:
            continue
        links = (
            '<div class="firmware-links" role="group" aria-label="Firmwares and support">'
            f'<a href="{root}../jazzy/" target="_top"><img class="firmware-mark" '
            f'src="{root}../jazzy/jazzy-mark.svg" alt="" width="14" height="14">JAZZY</a>'
            f'<a href="{root}#home" target="_top" aria-current="true">'
            f'<img class="firmware-mark" src="{root}rhythmer-mark.svg" alt="" '
            'width="14" height="14">RHYTHMER</a>'
            f'<a class="firmware-support" href="{root}#support" target="_top">SUPPORT ↗</a></div>'
        )
        if 'class="firmware-links"' in page:
            page = re.sub(r'<div class="firmware-links"[^>]*>.*?</div>', links, page, count=1, flags=re.S)
        else:
            page = re.sub(r'<div class="top-actions"[^>]*>.*?</div>', links, page, count=1, flags=re.S)
            page = re.sub(r'<a class="rhy-site-support"[^>]*>.*?</a>', links, page, count=1)
            page = re.sub(r'<aside class="jazzy-side">.*?</aside>\s*', '', page, flags=re.S)
        for css in ('firmware-links.css', 'jazzy-bridge.css'):
            if css not in page:
                page = page.replace('</head>', f'<link rel="stylesheet" href="{root}{css}">\n</head>', 1)
        mark = f'<img class="rhy-brand-mark" src="{root}rhythmer-mark.svg" alt="" width="27" height="27">'
        page = re.sub(r'(<a class="(?:brand|rhy-site-brand)"[^>]*>)(?:<span[^>]*>▥</span>|▥) RHYTHMER'
                      r'(?:<span class="brand-dot"></span>)?', lambda m: m[1] + mark + ' RHYTHMER', page)
        if not root:
            page = page.replace('href="assets/favicon.svg"', 'href="rhythmer-mark.svg"', 1)
            page = re.sub(r'app\.js\?v=[a-z0-9-]+', 'app.js?v=brand-preview', page)
        file.write_text(page)
    shutil.copyfile(ROOT / 'site/firmware-links.css', RHYTHMER / 'firmware-links.css')
    shutil.copyfile(ROOT / 'site/rhythmer-bridge.css', RHYTHMER / 'jazzy-bridge.css')
    shutil.copyfile(ROOT / 'site/rhythmer-mark.svg', RHYTHMER / 'rhythmer-mark.svg')


def update_rhythmer_motion():
    landing = RHYTHMER / 'landing.mjs'
    source = landing.read_text()
    source = re.sub(
        r'<img src="assets/boot/rhythmer-startup\.svg[^"]*"[^>]*>',
        '<div class="motion-clip"><img class="motion-moving" src="assets/boot/rhythmer-startup.webp?v=30s" alt="Rhythmer OS startup with six animated instruments" width="240" height="240"><img class="motion-still" src="assets/boot/rhythmer-startup.png" alt="Rhythmer OS startup screen" width="240" height="240"></div>',
        source,
    )
    source = source.replace('rhythmer-startup.webp"', 'rhythmer-startup.webp?v=30s"')
    landing.write_text(source)

    manual = RHYTHMER / 'manual.mjs'
    source = manual.read_text()
    start = source.index('const shot=')
    end = source.index('\n', start)
    marker = 'const animatedShots='
    if marker not in source:
        source = source[:start] + '''const animatedShots=['acid-generate','break-perform','drum-sound','gen-break','gen-target'];
const shot=(name,label)=>{
 const img=`<img src="assets/motion/${name}.png" width="240" height="240" loading="lazy" alt="${label}">`;
 const preview=animatedShots.includes(name)?`<picture><source media="(prefers-reduced-motion: no-preference)" srcset="assets/motion/${name}.webp">${img}</picture>`:img;
 return `<figure class="manual-shot">${preview}<figcaption>${label} · actual host-rendered firmware UI</figcaption></figure>`;
};''' + source[end:]
        manual.write_text(source)
    app = RHYTHMER / 'app.js'
    app.write_text(re.sub(r'((?:landing|manual)\.mjs)(?:\?v=[a-z0-9-]+)?(?=["\'])',
                          r'\1?v=brand-preview', app.read_text()))


if __name__ == '__main__':
    write_boot((BUILD / 'jazzy/site-startup').glob('startup-??.ppm'),
               PREVIEW / 'jazzy/assets/jazzy-startup')
    write_boot((BUILD / 'rhythmer/startup-motion-20261108.9').glob('startup-???.ppm'),
               RHYTHMER / 'assets/boot/rhythmer-startup')
    update_rhythmer_navigation()
    update_rhythmer_motion()
