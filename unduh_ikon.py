"""Unduh ikon Lucide (SVG) ke folder icons/ untuk dipakai build_slides.py."""
import concurrent.futures as cf
import re
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "icons"
OUT.mkdir(exist_ok=True)

BASE = "https://unpkg.com/lucide-static@0.469.0/icons/{}.svg"

NAMES = [
    "microscope", "target", "percent", "activity", "triangle-alert", "circle-alert",
    "lightbulb", "book-open", "scale", "layers", "crosshair", "database",
    "sliders-horizontal", "ruler", "eraser", "equal", "file-spreadsheet", "split",
    "repeat", "settings-2", "chart-no-axes-combined", "shield-check", "git-compare",
    "brain-circuit", "info", "sigma", "check-check", "flask-conical", "list-checks",
    "eye", "maximize-2", "minus", "link", "trophy", "chart-candlestick", "users",
    "scaling", "award", "trending-up", "shield-alert", "ban", "git-merge",
    "bar-chart-3", "badge-check", "route", "lock", "link-2",
]

FALLBACK = {
    "triangle-alert": ["alert-triangle"],
    "circle-alert": ["alert-circle"],
    "chart-no-axes-combined": ["line-chart", "trending-up"],
    "chart-candlestick": ["candlestick-chart"],
    "bar-chart-3": ["chart-column", "chart-bar", "bar-chart"],
    "settings-2": ["settings"],
    "file-spreadsheet": ["file-spreadsheet"],
}

def ambil(name):
    kandidat = [name] + FALLBACK.get(name, [])
    for k in kandidat:
        try:
            with urllib.request.urlopen(BASE.format(k), timeout=30) as r:
                svg = r.read().decode("utf-8")
            m = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S)
            inner = m.group(1).strip()
            (OUT / f"{name}.svg").write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">{inner}</svg>',
                encoding="utf-8")
            return name, k, len(inner)
        except Exception as e:  # noqa: BLE001
            last = e
    return name, None, str(last)

with cf.ThreadPoolExecutor(max_workers=10) as ex:
    hasil = list(ex.map(ambil, NAMES))

ok = [h for h in hasil if h[1]]
gagal = [h for h in hasil if not h[1]]
print(f"berhasil: {len(ok)}/{len(NAMES)}")
for n, k, _ in ok:
    if k != n:
        print(f"  alias: {n} -> {k}")
for n, _, err in gagal:
    print(f"  GAGAL: {n} ({err})")
