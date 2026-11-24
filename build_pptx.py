"""Rakit PPTX 16:9 dari 17 slide SVG.

Tiap slide = PNG resolusi tinggi sebagai fallback, lalu SVG vektor ditautkan
lewat ekstensi svgBlip supaya tajam di PowerPoint 2016+. Speaker notes dari
slides_spec.json disisipkan ke catatan tiap slide.
"""
import json
import re
import shutil
import zipfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright
from pptx import Presentation
from pptx.util import Emu

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "slides_spec.json").read_text(encoding="utf-8"))
PNG_DIR = Path(r"C:\Users\dedef\AppData\Local\Temp\opencode\ppt_png")
OUT = ROOT / "Perbandingan_Algoritma_Klasifikasi.pptx"
TMP = Path(r"C:\Users\dedef\AppData\Local\Temp\opencode\deck_raw.pptx")

N = SPEC["meta"]["total_slides"]
SCALE = 2  # PNG 2666x1500 px

# 1. Render PNG tiap slide
PNG_DIR.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1333, "height": 750},
                    device_scale_factor=SCALE)
    for i in range(1, N + 1):
        svg = (ROOT / f"slide_{i}.svg").resolve()
        pg.goto(svg.as_uri())
        pg.wait_for_timeout(150)
        pg.screenshot(path=str(PNG_DIR / f"slide_{i}.png"))
        print("render", svg.name)
    b.close()

# 2. Susun PPTX dasar berisi PNG penuh slide + speaker notes
notes = {s["id"]: s.get("speaker_notes", "") for s in SPEC["slides"]}
prs = Presentation()
prs.slide_width = Emu(12192000)   # 13,333 in
prs.slide_height = Emu(6858000)   # 7,5 in
blank = prs.slide_layouts[6]
for i in range(1, N + 1):
    slide = prs.slides.add_slide(blank)
    slide.shapes.add_picture(str(PNG_DIR / f"slide_{i}.png"), 0, 0,
                             width=prs.slide_width, height=prs.slide_height)
    slide.notes_slide.notes_text_frame.text = notes.get(i, "")
prs.save(TMP)

# 3. Sisipkan SVG ke paket (fallback PNG tetap ada)
SVG_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
ASVG = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
REL_SVG = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

zin = zipfile.ZipFile(TMP)
items = {name: zin.read(name) for name in zin.namelist()}
zin.close()

ct = items["[Content_Types].xml"].decode("utf-8")
if "image/svg+xml" not in ct:
    ct = ct.replace("</Types>",
                    '<Default Extension="svg" ContentType="image/svg+xml"/></Types>')
items["[Content_Types].xml"] = ct.encode("utf-8")

for i in range(1, N + 1):
    slide_name = f"ppt/slides/slide{i}.xml"
    rels_name = f"ppt/slides/_rels/slide{i}.xml.rels"
    media_name = f"ppt/media/slideart{i}.svg"

    xml = items[slide_name].decode("utf-8")
    rid_svg = f"rIdSvg{i}"
    xml = re.sub(
        r'<a:blip r:embed="([^"]+)"\s*/>',
        lambda m: (f'<a:blip r:embed="{m.group(1)}"><a:extLst><a:ext uri="{SVG_URI}">'
                   f'<asvg:svgBlip xmlns:asvg="{ASVG}" r:embed="{rid_svg}"/>'
                   f'</a:ext></a:extLst></a:blip>'),
        xml, count=1)
    items[slide_name] = xml.encode("utf-8")

    rels = items[rels_name].decode("utf-8")
    rels = rels.replace("</Relationships>",
                        f'<Relationship Id="{rid_svg}" Type="{REL_SVG}" '
                        f'Target="../media/slideart{i}.svg"/></Relationships>')
    items[rels_name] = rels.encode("utf-8")
    items[media_name] = (ROOT / f"slide_{i}.svg").read_bytes()

zout = zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED)
for name, data in items.items():
    zout.writestr(name, data)
zout.close()

print("selesai:", OUT.name, f"({OUT.stat().st_size / 1024 / 1024:.1f} MB)")
