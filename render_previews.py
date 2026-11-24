"""Render semua slide SVG ke PNG pratinjau di folder temp."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
TMP = Path(r"C:\Users\dedef\AppData\Local\Temp\opencode\ppt_preview")
TMP.mkdir(exist_ok=True)

only = sys.argv[1:] if len(sys.argv) > 1 else None

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1333, "height": 750}, device_scale_factor=2)
    for svg in sorted(ROOT.glob("slide_*.svg"),
                      key=lambda f: int(f.stem.split("_")[1])):
        if only and svg.stem not in only:
            continue
        pg.goto(svg.resolve().as_uri())
        pg.wait_for_timeout(200)
        out = TMP / (svg.stem + ".png")
        pg.screenshot(path=str(out))
        print(out.name)
    b.close()
