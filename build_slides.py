#!/usr/bin/env python3
"""build_slides.py — generator slide SVG dari slides_spec.json.

Membaca spesifikasi (koordinat dalam inci, tema "Clinical Clean", blok per slide)
lalu menulis slide_1.svg ... slide_N.svg di folder ini, ditambah speaker_notes.md.

Slide bertanda "custom_svg": true di spesifikasi adalah slide buatan tangan
(pecahan slide 5, slide_5.svg ... slide_11.svg); file-nya tidak ditimpa selama
masih ada, hanya catatan pembicara yang diperbarui.

Pemakaian:  python build_slides.py
"""
from __future__ import annotations

import base64
import json
import math
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "slides_spec.json").read_text(encoding="utf-8"))
ICONS = ROOT / "icons"
PLOTS = ROOT / "projek_breast_cancer_R" / "output" / "plots"

# ---------------------------------------------------------------- geometri
# 100 unit SVG = 1 inci; font dalam pt.
U = 100.0
PT = U / 72.0
W, H = 1333.33, 750.0

C = SPEC["theme"]["colors"]
COMP = SPEC["theme"]["components"]
TYP = SPEC["theme"]["typography"]
SCALE = TYP["scale_pt"]
LH = TYP["line_height"]

HEAD = "'Poppins','Calibri',Arial,sans-serif"
BODY = "'Inter','Calibri',Arial,sans-serif"
MONO = "'JetBrains Mono',Consolas,'Calibri',monospace"

FRAME = "#B9CCD8"   # garis luar kartu — lebih tegas dari border tema


def u(v: float) -> float:
    return v * U


def pt(v: float) -> float:
    return v * PT


def color(name: str) -> str:
    """'accent_malignant' -> hex, atau teruskan '#xxxxxx'."""
    return name if str(name).startswith("#") else C[str(name)]


def lighten(hex_color: str, t: float = 0.45) -> str:
    """Campur dengan putih sebesar t (0-1) agar terbaca di atas bidang gelap."""
    h = hex_color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    mixed = [int(v + (255 - v) * t) for v in rgb]
    return "#%02X%02X%02X" % tuple(mixed)


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ------------------------------------------------------- lebar teks (Arial)
_AW = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667,
    "'": 191, "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333,
    ".": 278, "/": 278, ":": 278, ";": 278, "<": 584, "=": 584, ">": 584,
    "?": 556, "@": 1015, "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556,
    "`": 333, "{": 334, "|": 260, "}": 334, "~": 584,
    "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722,
    "O": 778, "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722,
    "V": 667, "W": 944, "X": 667, "Y": 667, "Z": 611,
    "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556,
    "h": 556, "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556,
    "o": 556, "p": 556, "q": 556, "r": 333, "s": 500, "t": 278, "u": 556,
    "v": 500, "w": 722, "x": 500, "y": 500, "z": 500,
    "\u2022": 350, "\u2013": 556, "\u2014": 1000, "\u2265": 549, "\u2264": 549,
}
for _d in "0123456789":
    _AW[_d] = 556


def char_w(ch: str, bold: bool = False) -> float:
    w = _AW.get(ch, 520) / 1000.0
    return w * (1.06 if bold else 1.0)


def text_w(s: str, size_u: float, bold: bool = False) -> float:
    return sum(char_w(c, bold) for c in str(s)) * size_u


def wrap(text: str, max_w: float, size_u: float, bold: bool = False) -> list[str]:
    words = str(text).split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = words[0]
    for wd in words[1:]:
        cand = cur + " " + wd
        if text_w(cand, size_u, bold) <= max_w:
            cur = cand
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    return lines


def fit_lines(text: str, w: float, h: float, base_pt: float,
              bold: bool = False, min_pt: float = 10.0):
    """Pecah baris + kecilkan font (turun 0.5pt) sampai muat tinggi h (inci)."""
    size = base_pt
    while True:
        lines = wrap(text, u(w), pt(size), bold)
        if len(lines) * pt(size) * LH <= u(h) or size <= min_pt:
            return lines, size
        size -= 0.5


# --------------------------------------------------------------- primitif
def rect(x, y, w, h, fill, rx=0.0, stroke=None, sw=0.0, opacity=None,
         shadow=False, fill_opacity=None) -> str:
    out = ""
    if shadow:
        # bayangan lembut dari lapisan rect semi-transparan —
        # filter SVG (feDropShadow) tidak didukung PowerPoint
        out += (f'<rect x="{u(x - 0.008):.2f}" y="{u(y + 0.028):.2f}" '
                f'width="{u(w + 0.016):.2f}" height="{u(h):.2f}" '
                f'fill="#1B2A33" fill-opacity="0.045" '
                f'rx="{u(rx or 0.12):.2f}"/>'
                f'<rect x="{u(x):.2f}" y="{u(y + 0.012):.2f}" '
                f'width="{u(w):.2f}" height="{u(h):.2f}" '
                f'fill="#1B2A33" fill-opacity="0.05" '
                f'rx="{u(rx or 0.12):.2f}"/>')
    s = (f'<rect x="{u(x):.2f}" y="{u(y):.2f}" width="{u(w):.2f}" '
         f'height="{u(h):.2f}" fill="{fill}"')
    if rx:
        s += f' rx="{u(rx):.2f}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw or pt(1):.2f}"'
    if opacity is not None:
        s += f' opacity="{opacity}"'
    if fill_opacity is not None:
        s += f' fill-opacity="{fill_opacity}"'
    return out + s + "/>"


def line(x1, y1, x2, y2, stroke, sw=1.0, opacity=None) -> str:
    s = (f'<line x1="{u(x1):.2f}" y1="{u(y1):.2f}" x2="{u(x2):.2f}" '
         f'y2="{u(y2):.2f}" stroke="{stroke}" stroke-width="{sw:.2f}"')
    if opacity is not None:
        s += f' opacity="{opacity}"'
    return s + "/>"


def text(x, y, s, size_pt, fill, weight="400", family=BODY,
         anchor="start", ls=None, opacity=None) -> str:
    a = (f'<text x="{u(x):.2f}" y="{u(y):.2f}" font-family="{family}" '
         f'font-size="{pt(size_pt):.2f}" font-weight="{weight}" fill="{fill}"')
    if anchor != "start":
        a += f' text-anchor="{anchor}"'
    if ls:
        a += f' letter-spacing="{pt(ls):.2f}"'
    if opacity is not None:
        a += f' opacity="{opacity}"'
    return a + f">{esc(s)}</text>"


def text_block(x, y_top, w, lines, size_pt, fill, weight="400",
               family=BODY, anchor="start", max_lines=None) -> str:
    lh = pt(size_pt) * LH / U  # tinggi baris dalam inci
    out = []
    for i, ln in enumerate(lines[:max_lines] if max_lines else lines):
        out.append(text(x, y_top + 0.8 * lh + i * lh, ln, size_pt, fill,
                        weight, family, anchor))
    return "".join(out)


def blc(cy: float, size_pt: float) -> float:
    """Baseline agar teks size_pt tampak terpusat vertikal di cy (inci)."""
    return cy + 0.36 * size_pt / 72.0


# ------------------------------------------------------------------- ikon
_ICON_CACHE: dict[str, str] = {}


def icon_inner(name: str) -> str:
    if name not in _ICON_CACHE:
        svg = (ICONS / f"{name}.svg").read_text(encoding="utf-8")
        m = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S)
        _ICON_CACHE[name] = m.group(1).strip()
    return _ICON_CACHE[name]


def icon(name: str, x: float, y: float, size_u: float, color_: str,
         stroke_pt: float = 2.0) -> str:
    s = size_u / 24.0
    sw = pt(stroke_pt) / s
    return (f'<g transform="translate({u(x):.2f},{u(y):.2f}) scale({s:.4f})" '
            f'fill="none" stroke="{color_}" stroke-width="{sw:.3f}" '
            f'stroke-linecap="round" stroke-linejoin="round">'
            f"{icon_inner(name)}</g>")


def icon_badge(cx: float, cy: float, d_in: float, accent: str, name: str,
               icon_ratio: float = 0.58, fill_opacity: float = 0.15) -> str:
    r = u(d_in) / 2
    out = [f'<circle cx="{u(cx):.2f}" cy="{u(cy):.2f}" r="{r:.2f}" '
           f'fill="{accent}" fill-opacity="{fill_opacity}"/>']
    isz = u(d_in) * icon_ratio
    out.append(icon(name, cx - d_in * icon_ratio / 2,
                    cy - d_in * icon_ratio / 2, isz, accent))
    return "".join(out)


def card(x, y, w, h, accent=None, fill=None) -> str:
    out = [rect(x, y, w, h, fill or C["surface"], rx=0.12,
                stroke=FRAME, sw=pt(1.2), shadow=True)]
    if accent:
        out.append(rect(x, y + 0.12, 0.07, h - 0.24, color(accent)))
    return "".join(out)


# ------------------------------------------------------------ format angka
def fmt_label(v) -> str:
    if isinstance(v, int):
        return str(v)
    f = float(v)
    if abs(f) >= 10:          # nilai besar: 1 desimal (458,4 / 932,0)
        return f"{f:.1f}".replace(".", ",")
    return f"{f:.4f}".replace(".", ",")   # probabilitas/metrik: 4 desimal


def fmt_tick(v: float, step: float) -> str:
    if step >= 1 and float(v).is_integer():
        return str(int(v))
    dec = 2 if step >= 0.01 else 3
    return f"{v:.{dec}f}".replace(".", ",")


def nice_step(span: float) -> float:
    for s in (0.005, 0.01, 0.02, 0.025, 0.05, 0.1, 0.2, 0.25, 0.5,
              1, 2, 2.5, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if span / s <= 7:
            return s
    return span / 7


# ================================================================ BLOK-BLOK
def b_stat_card(b) -> str:
    acc = color(b["accent"])
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    out = [card(x, y, w, h, b["accent"])]
    d = 0.56
    out.append(icon_badge(x + w - 0.18 - d / 2, y + 0.18 + d / 2, d, acc,
                          b["icon"]))
    # nilai besar (kecilkan bila melebihi lebar)
    avail = u(w - 0.36 - d - 0.16)
    vs = SCALE["stat_number"]
    while text_w(b["value"], pt(vs), True) > avail and vs > 24:
        vs -= 1
    out.append(text(x + 0.2, y + 0.78, b["value"], vs, C["text_primary"],
                    "700", HEAD))
    lines = wrap(b["label"], u(w - 0.42), pt(SCALE["stat_label"]))
    out.append(text_block(x + 0.2, y + 0.92, w - 0.42, lines,
                          SCALE["stat_label"], C["text_secondary"]))
    return "".join(out)


def _icon_card_body(x, y, w, h, b, body_top):
    """Isi kartu ikon: 'text' atau 'bullets', auto-shrink sampai muat."""
    out = []
    avail_h = h - (body_top - y) - (0.08 if b.get("title") else 0.12)
    if not b.get("title") and b.get("icon"):
        tx0 = x + 0.92          # teks di kanan badge (kartu tanpa judul)
        tw = w - 0.92 - 0.18
    else:
        tx0 = x + 0.2
        tw = w - 0.36
    if b.get("bullets"):
        items = b["bullets"]
        size = SCALE["body_dense"]
        while True:
            lh = pt(size) * LH / U
            total = 0.0
            wrapped = []
            for it in items:
                ls = wrap(it, u(tw - 0.22), pt(size))
                wrapped.append(ls)
                total += len(ls) * lh + 0.07
            total -= 0.07
            if total <= avail_h or size <= 10:
                break
            size -= 0.5
        slack = max(0.0, avail_h - total)
        extra_gap = min(0.08, slack / max(1, len(items) - 1) * 0.45)
        item_gap = 0.07 + extra_gap
        yy = body_top + min(0.06, slack * 0.2)
        for ls in wrapped:
            out.append(text(tx0 + 0.02, yy + 0.8 * lh, "\u2022", size,
                            acc_or(b, C["text_secondary"]), "600"))
            for i, ln in enumerate(ls):
                out.append(text(tx0 + 0.22, yy + 0.8 * lh + i * lh, ln, size,
                                C["text_primary"]))
            yy += len(ls) * lh + item_gap
    elif b.get("text"):
        lines, size = fit_lines(b["text"], tw, avail_h, SCALE["body_dense"])
        lh = pt(size) * LH / U
        text_h = len(lines) * lh
        rem_h = h - (body_top - y)
        if b.get("title"):
            top = body_top + max(0.04, (rem_h - text_h) / 2)
        else:
            top = body_top + max(0.0, (avail_h - text_h) / 2)
        out.append(text_block(tx0, top, tw, lines, size,
                              C["text_primary"]))
    return "".join(out)


def acc_or(b, default):
    return color(b["accent"]) if b.get("accent") else default


def b_icon_card(b) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    acc = color(b["accent"])
    out = [card(x, y, w, h, b["accent"])]
    d = 0.56
    has_title = bool(b.get("title"))
    if has_title or b.get("icon"):
        cy = y + 0.18 + d / 2 if has_title else y + h / 2
        out.append(icon_badge(x + 0.18 + d / 2, cy, d, acc, b.get("icon", "info")))
    if has_title:
        tl = wrap(b["title"], u(w - 0.36 - d - 0.16), pt(SCALE["card_title"]), True)
        lh_title = pt(SCALE["card_title"]) * LH / U
        title_y_top = blc(cy, SCALE["card_title"]) - 0.8 * lh_title - (len(tl) - 1) * lh_title / 2
        out.append(text_block(x + 0.2 + d + 0.16, title_y_top,
                              w - 0.36 - d - 0.16, tl, SCALE["card_title"],
                              C["text_primary"], "600", HEAD))
        title_bottom = (title_y_top - y) + len(tl) * lh_title
        header_bottom = max(0.18 + d, title_bottom)
        body_top = y + header_bottom
    else:
        body_top = y + 0.14
    out.append(_icon_card_body(x, y, w, h, b, body_top))
    return "".join(out)


def b_question_card(b) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    acc = color(b["accent"])
    out = [card(x, y, w, h, b["accent"])]
    # pil nomor
    pill_w = text_w(b["number"], pt(11), True) / U + 0.34
    out.append(rect(x + 0.2, y + 0.18, pill_w, 0.32, acc, rx=0.16))
    out.append(text(x + 0.2 + pill_w / 2, y + 0.18 + 0.215, b["number"], 11,
                    C["text_on_dark"], "700", HEAD, anchor="middle"))
    d = 0.5
    out.append(icon_badge(x + w - 0.2 - d / 2, y + 0.18 + 0.16, d, acc,
                          b["icon"]))
    tl = wrap(b["title"], u(w - 0.4), pt(SCALE["card_title"]), True)
    out.append(text_block(x + 0.2, y + 0.62, w - 0.4, tl, SCALE["card_title"],
                          C["text_primary"], "700", HEAD))
    body_top = y + 0.62 + len(tl) * pt(SCALE["card_title"]) * LH / U + 0.1
    out.append(_icon_card_body(x, y, w, h, b, body_top))
    return "".join(out)


def b_callout(b) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    acc = color(b["accent"])
    out = [rect(x, y, w, h, acc, rx=0.1, fill_opacity=0.12),
           rect(x, y + 0.06, 0.07, h - 0.12, acc, rx=0.035)]
    d = 0.56
    out.append(icon_badge(x + 0.24 + d / 2, y + h / 2, d, acc,
                          b.get("icon", "info")))
    tw = w - 0.24 - d - 0.2 - 0.18
    lines, size = fit_lines(b["text"], tw, h - 0.2, SCALE["body_dense"])
    lh = pt(size) * LH / U
    top = y + (h - len(lines) * lh) / 2
    out.append(text_block(x + 0.24 + d + 0.2, top, tw, lines, size,
                          C["text_primary"]))
    return "".join(out)


def b_highlight_banner(b) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    acc = color(b["accent"])
    out = [rect(x, y, w, h, acc, rx=0.1, shadow=True)]
    d = 0.6
    out.append(f'<circle cx="{u(x + 0.32 + d / 2):.2f}" cy="{u(y + h / 2):.2f}" '
               f'r="{u(d / 2):.2f}" fill="#FFFFFF" fill-opacity="0.2"/>')
    out.append(icon(b["icon"], x + 0.32 + d * 0.21, y + h / 2 - d * 0.29,
                    u(d * 0.58), "#FFFFFF"))
    tw = w - 0.32 - d - 0.24 - 0.2
    lines, size = fit_lines(b["text"], tw, h - 0.16, 14, bold=True)
    lh = pt(size) * LH / U
    top = y + (h - len(lines) * lh) / 2
    out.append(text_block(x + 0.32 + d + 0.24, top, tw, lines, size,
                          "#FFFFFF", "600", BODY))
    return "".join(out)


# ------------------------------------------------------------------ tabel
def b_table(b) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    cols, rows = b["columns"], b["rows"]
    out = []
    # kaption di atas
    cap = wrap(b.get("caption", ""), u(w), pt(SCALE["caption"]), True)
    out.append(text_block(x, y, w, cap, SCALE["caption"],
                          C["text_primary"], "600", BODY))
    ty = y + 0.34
    th = h - 0.34
    # lebar kolom proporsional isi (satuan inci)
    weights = []
    for ci in range(len(cols)):
        m = text_w(cols[ci], pt(SCALE["table_header"]), True)
        for r in rows:
            m = max(m, text_w(r[ci], pt(SCALE["table_cell"])))
        weights.append(m + u(0.3))
    tot = sum(weights)
    widths = [ww / tot * w for ww in weights]
    nrow = len(rows)
    hh = min(0.4, th * 0.22)
    rh = (th - hh) / nrow
    cid = f"tbl{int(u(x))}_{int(u(y))}"
    out.append(f'<clipPath id="{cid}"><rect x="{u(x):.2f}" y="{u(ty):.2f}" '
               f'width="{u(w):.2f}" height="{u(th):.2f}" rx="6"/></clipPath>')
    out.append(rect(x, ty, w, th, C["surface"], rx=0.06,
                    stroke=FRAME, sw=pt(1.2), shadow=True))
    out.append(f'<g clip-path="url(#{cid})">')
    # header
    out.append(rect(x, ty, w, hh, C["primary"]))
    cx = x
    for ci, cname in enumerate(cols):
        al = b.get("align", ["left"] * len(cols))[ci]
        col_acc = (b.get("column_accent") or {}).get(str(ci))
        fill = lighten(color(col_acc), 0.45) if col_acc else C["text_on_dark"]
        tx = cx + 0.14 if al == "left" else cx + widths[ci] - 0.14
        out.append(text(tx, blc(ty + hh / 2, SCALE["table_header"]), cname,
                        SCALE["table_header"], fill, "600", BODY,
                        anchor="start" if al == "left" else "end"))
        cx += widths[ci]
    # badan
    best = {tuple(bc) for bc in b.get("best_cells", [])}
    hi = set(b.get("highlight_rows", []))
    rac = b.get("row_accent_colors") or []
    for ri, row in enumerate(rows):
        ry = ty + hh + ri * rh
        if ri in hi:
            out.append(rect(x, ry, w, rh,
                            color(COMP["table"]["highlight_fill"])))
        elif ri % 2 == 1:
            out.append(rect(x, ry, w, rh,
                            color(COMP["table"]["row_alt_fill"])))
        cx = x
        for ci, val in enumerate(row):
            al = b.get("align", ["left"] * len(cols))[ci]
            col_acc = (b.get("column_accent") or {}).get(str(ci))
            is_best = (ri, ci) in best
            fill = color("accent_malignant") if is_best else (
                color(col_acc) if col_acc else C["text_primary"])
            weight = "700" if is_best else ("600" if ri in hi else "400")
            pad_x = 0.14
            if ci == 0 and rac:
                out.append(f'<circle cx="{u(cx + 0.17):.2f}" '
                           f'cy="{u(ry + rh / 2):.2f}" r="{u(0.055):.2f}" '
                           f'fill="{rac[ri]}"/>')
                pad_x = 0.32
            tx = cx + pad_x if al == "left" else cx + widths[ci] - 0.14
            fs = SCALE["table_cell"]
            while (text_w(val, pt(fs), weight != "400")
                   > u(widths[ci] - pad_x - 0.1) and fs > 10):
                fs -= 0.5
            out.append(text(tx, blc(ry + rh / 2, fs), val, fs, fill,
                            weight, BODY,
                            anchor="start" if al == "left" else "end"))
            cx += widths[ci]
        if ri < nrow - 1:
            out.append(line(x, ry + rh, x + w, ry + rh,
                            C["border"], sw=pt(0.75), opacity=0.7))
    out.append("</g>")
    # garis luar digambar ulang di atas baris: rapi walau clipPath
    # tidak didukung renderer target (mis. PowerPoint)
    out.append(rect(x, ty, w, th, "none", rx=0.06,
                    stroke=FRAME, sw=pt(1.2)))
    return "".join(out)


# ------------------------------------------------------------------ chart
def _chart_frame(b):
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    out = [card(x, y, w, h)]
    out.append(text(x + 0.18, y + 0.4, b.get("title", ""), 12,
                    C["text_primary"], "600", HEAD))
    return out


def _legend(out, b, px0, px1, ybot):
    if not b.get("legend"):
        return
    items = [(s["name"], s.get("color") or (s.get("colors") or [C["primary"]])[0])
             for s in b["series"]]
    wtot = sum(text_w(nm, pt(10)) / U + 0.36 for nm, _ in items) - 0.16
    cx = px0 + ((px1 - px0) - wtot) / 2
    for nm, col in items:
        out.append(f'<circle cx="{u(cx + 0.07):.2f}" cy="{u(ybot):.2f}" '
                   f'r="{u(0.055):.2f}" fill="{col}"/>')
        out.append(text(cx + 0.21, ybot + 0.037, nm, 10,
                        C["text_secondary"]))
        cx += text_w(nm, pt(10)) / U + 0.36


def b_chart(b) -> str:
    ct = b["chart_type"]
    if ct == "bar_horizontal":
        return _chart_hbar(b)
    return _chart_vbar(b, stacked=(ct == "bar_stacked"))


def _chart_vbar(b, stacked=False) -> str:
    out = _chart_frame(b)
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    cats, series = b["categories"], b["series"]
    vals_max = max(sum(s["values"][i] for s in series) if stacked
                   else max(s["values"][i] for s in series)
                   for i in range(len(cats)))
    vmin = b.get("axis_min", 0.0)
    vmax = b.get("axis_max")
    if vmax is None:
        step = nice_step((vals_max * 1.12 - vmin) or 1)
        vmax = math.ceil(vals_max * 1.12 / step) * step
    step = nice_step(vmax - vmin)
    pad_l, pad_r, pad_t, pad_b = 0.66, 0.18, 0.62, 0.4
    if b.get("legend"):
        pad_b += 0.32
    if b.get("y_title"):
        pad_l += 0.28
    px0, px1 = x + pad_l, x + w - pad_r
    py0, py1 = y + pad_t, y + h - pad_b
    pw, ph = px1 - px0, py1 - py0

    def ypos(v):
        return py1 - (v - vmin) / (vmax - vmin) * ph

    # gridline + label sumbu y
    t = vmin
    while t <= vmax + 1e-9:
        yy = ypos(t)
        out.append(line(px0, yy, px1, yy, C["border"], sw=pt(0.75),
                        opacity=0.8 if t > vmin else 1))
        out.append(text(px0 - 0.1, blc(yy, 10), fmt_tick(t, step), 10,
                        C["text_secondary"], anchor="end"))
        t += step
    if b.get("y_title"):
        cx = x + 0.3
        cy = (py0 + py1) / 2
        out.append(f'<text transform="translate({u(cx):.2f},{u(cy):.2f}) '
                   f'rotate(-90)" text-anchor="middle" font-family="{BODY}" '
                   f'font-size="{pt(9.5):.2f}" fill="{C["text_secondary"]}">'
                   f'{esc(b["y_title"])}</text>')

    gw = pw / len(cats)
    nser = len(series)
    per_cat_colors = "colors" in series[0]
    for ci, cat in enumerate(cats):
        gx = px0 + ci * gw
        if stacked:
            bw = gw * 0.5
            bx = gx + (gw - bw) / 2
            acc_y = py1
            for s in series:
                v = s["values"][ci]
                col = (s.get("colors") or [s.get("color")] * len(cats))[ci]
                seg_h = v / (vmax - vmin) * ph
                seg_y = acc_y - seg_h
                if v > 0:
                    out.append(rect(bx, seg_y, bw, seg_h, col, rx=0.03))
                    if b.get("data_labels") and seg_h >= 0.24:
                        out.append(text(bx + bw / 2, blc(seg_y + seg_h / 2, 10),
                                        fmt_label(v), 10, "#FFFFFF", "700",
                                        BODY, anchor="middle"))
                acc_y = seg_y
        else:
            bw = gw * 0.72 / nser
            for si, s in enumerate(series):
                v = s["values"][ci]
                col = (s.get("colors") or [s.get("color")] * len(cats))[ci]
                bx = gx + (gw - bw * nser) / 2 + si * bw
                yv = ypos(v)
                out.append(rect(bx, yv, bw, py1 - yv, col, rx=0.03))
                if b.get("data_labels"):
                    out.append(text(bx + bw / 2, yv - 0.07, fmt_label(v), 10,
                                    C["text_primary"], "600", BODY,
                                    anchor="middle"))
        # label kategori
        cfill = C["text_secondary"]
        if per_cat_colors and nser == 1:
            cfill = series[0]["colors"][ci]
        out.append(text(gx + gw / 2, py1 + 0.24, cat, 10, cfill,
                        "600" if per_cat_colors else "400", BODY,
                        anchor="middle"))
    _legend(out, b, px0, px1, y + h - 0.18)
    return "".join(out)


def _chart_hbar(b) -> str:
    out = _chart_frame(b)
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    cats, series = b["categories"], b["series"]
    s = series[0]
    vals = s["values"]
    vmin = b.get("axis_min", 0.0)
    vmax = b.get("axis_max", max(vals) * 1.05)
    step = nice_step(vmax - vmin)
    pad_l = max(0.95, max(text_w(c, pt(10)) for c in cats) / U + 0.3)
    pad_r, pad_t, pad_b = 0.85, 0.62, 0.42
    px0, px1 = x + pad_l, x + w - pad_r
    py0, py1 = y + pad_t, y + h - pad_b
    pw, ph = px1 - px0, py1 - py0

    def xpos(v):
        return px0 + (v - vmin) / (vmax - vmin) * pw

    t = vmin
    while t <= vmax + 1e-9:
        xx = xpos(t)
        out.append(line(xx, py0, xx, py1, C["border"], sw=pt(0.75),
                        opacity=0.8))
        out.append(text(xx, py1 + 0.24, fmt_tick(t, step), 10,
                        C["text_secondary"], anchor="middle"))
        t += step
    rows_h = ph / len(cats)
    colors_ = s.get("colors") or [s.get("color", C["primary"])] * len(cats)
    for ci, cat in enumerate(cats):
        cy = py0 + ci * rows_h + rows_h / 2
        bh = rows_h * 0.56
        xv = xpos(vals[ci])
        out.append(rect(px0, cy - bh / 2, xv - px0, bh, colors_[ci], rx=0.03))
        out.append(text(px0 - 0.12, blc(cy, 10), cat, 10, C["text_primary"],
                        "400", BODY, anchor="end"))
        if b.get("data_labels"):
            out.append(text(xv + 0.08, blc(cy, 10), fmt_label(vals[ci]), 10,
                            C["text_primary"], "600", BODY))
    return "".join(out)


# ------------------------------------------------------- process/formula
def b_process_flow(b) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    steps = b["steps"]
    n = len(steps)
    gap = 0.21
    cw = (w - gap * (n - 1)) / n
    out = []
    for i, st in enumerate(steps):
        sx = x + i * (cw + gap)
        acc = color(st["accent"])
        out.append(rect(sx, y, cw, h, C["surface"], rx=0.1,
                        stroke=FRAME, sw=pt(1.2), shadow=True))
        # nomor
        out.append(f'<circle cx="{u(sx + 0.28):.2f}" cy="{u(y + 0.32):.2f}" '
                   f'r="{u(0.16):.2f}" fill="{acc}"/>')
        out.append(text(sx + 0.28, y + 0.32 + 0.055, str(st["n"]), 11.5,
                        "#FFFFFF", "700", HEAD, anchor="middle"))
        d = 0.48
        out.append(icon_badge(sx + cw - 0.18 - d / 2, y + 0.32, d, acc,
                              st["icon"], icon_ratio=0.56))
        tl = wrap(st["title"], u(cw - 0.32), pt(12), True)
        title_h = len(tl) * pt(12) * LH / U
        title_y = y + 0.66
        out.append(text_block(sx + 0.16, title_y, cw - 0.32, tl, 12,
                              C["text_primary"], "600", HEAD))
        rem_h = h - 0.66 - title_h - 0.08 - 0.14
        lines, size = fit_lines(st["text"], cw - 0.32, rem_h, 10.5)
        by = title_y + title_h + 0.08
        out.append(text_block(sx + 0.16, by, cw - 0.32, lines, size,
                              C["text_secondary"]))
        if i < n - 1:
            ax = sx + cw + gap / 2
            out.append(f'<path d="M {u(ax - 0.045):.2f} {u(y + 0.32 - 0.08):.2f} '
                       f'L {u(ax + 0.05):.2f} {u(y + 0.32):.2f} '
                       f'L {u(ax - 0.045):.2f} {u(y + 0.32 + 0.08):.2f}" '
                       f'fill="none" stroke="{C["text_secondary"]}" '
                       f'stroke-width="{pt(1.6):.2f}" stroke-linecap="round" '
                       f'stroke-linejoin="round" opacity="0.75"/>')
    return "".join(out)


def b_formula_flow(b) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    out = []
    chip_w, gap = 1.95, 0.12
    cy_mid = y + h / 2
    inp = b["inputs"]
    for i, ch in enumerate(inp):
        cx = x + i * (chip_w + gap)
        chy = cy_mid - 0.65
        out.append(rect(cx, chy, chip_w, 1.3, C["surface"], rx=0.1,
                        stroke=FRAME, sw=pt(1.2), shadow=True))
        out.append(rect(cx, chy + 0.12, 0.07, 1.06, ch["color"]))
        out.append(text(cx + 0.2, chy + 0.42, ch["label"], 12, ch["color"],
                        "700", HEAD))
        out.append(text(cx + 0.2, chy + 0.72, ch["text"], 10.5,
                        C["text_primary"]))
    # panah 1
    def arrow(ax):
        out.append(f'<path d="M {u(ax):.2f} {u(cy_mid):.2f} '
                   f'L {u(ax + 0.18):.2f} {u(cy_mid):.2f}" '
                   f'stroke="{C["text_secondary"]}" stroke-width="{pt(2):.2f}" '
                   f'stroke-linecap="round"/>'
                   f'<path d="M {u(ax + 0.11):.2f} {u(cy_mid - 0.08):.2f} '
                   f'L {u(ax + 0.22):.2f} {u(cy_mid):.2f} '
                   f'L {u(ax + 0.11):.2f} {u(cy_mid + 0.08):.2f}" '
                   f'fill="none" stroke="{C["text_secondary"]}" '
                   f'stroke-width="{pt(2):.2f}" stroke-linecap="round" '
                   f'stroke-linejoin="round"/>')

    x_after = x + 4 * chip_w + 3 * gap
    arrow(x_after + 0.02)
    # operator
    op = b["operator"]
    ocx = x_after + 0.3 + 0.62
    out.append(f'<circle cx="{u(ocx):.2f}" cy="{u(cy_mid - 0.18):.2f}" '
               f'r="{u(0.4):.2f}" fill="{C["surface_alt"]}" '
               f'stroke="{C["primary"]}" stroke-width="{pt(1):.2f}"/>')
    out.append(icon(op["icon"], ocx - 0.19, cy_mid - 0.37, u(0.38), C["primary"]))
    ol = wrap(op["text"], u(1.24), pt(10))
    out.append(text_block(ocx, cy_mid + 0.32, 1.24, ol, 10,
                          C["text_secondary"], anchor="middle"))
    # panah 2
    arrow(ocx + 0.4 + 0.12)
    # output
    ox = ocx + 0.4 + 0.12 + 0.34
    och = b["output"]
    ow = x + w - ox
    out.append(rect(ox, cy_mid - 0.75, ow, 1.5, C["surface"], rx=0.1,
                    stroke=FRAME, sw=pt(1.2), shadow=True))
    out.append(rect(ox, cy_mid - 0.63, 0.07, 1.26, och["color"]))
    out.append(text(ox + 0.2, cy_mid - 0.32, och["label"], 12, och["color"],
                    "700", HEAD))
    ol2 = wrap(och["text"], u(ow - 0.4), pt(10.5))
    out.append(text_block(ox + 0.2, cy_mid - 0.12, ow - 0.4, ol2, 10.5,
                          C["text_primary"]))
    return "".join(out)


def b_ranked_list(b) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    acc = color(b["accent"])
    out = [card(x, y, w, h)]
    out.append(text(x + 0.24, y + 0.44, b["title"], SCALE["card_title"],
                    C["text_primary"], "700", HEAD))
    items = b["items"]
    top = y + 0.72
    footer_h = 0.42
    rh = (h - (top - y) - footer_h) / len(items)
    for i, it in enumerate(items):
        ry = top + i * rh
        cy = ry + rh / 2
        out.append(f'<circle cx="{u(x + 0.42):.2f}" cy="{u(cy):.2f}" '
                   f'r="{u(0.17):.2f}" fill="{acc}"/>')
        out.append(text(x + 0.42, cy + 0.055, str(it["rank"]), 11, "#FFFFFF",
                        "700", HEAD, anchor="middle"))
        out.append(text(x + 0.72, cy + 0.055, it["name"], 12,
                        C["text_primary"], "400", MONO))
        tag = it.get("tag")
        if tag:
            tw = text_w(tag, pt(10)) / U + 0.26
            out.append(rect(x + w - 0.24 - tw, cy - 0.13, tw, 0.26,
                            C["surface_alt"], rx=0.13))
            out.append(text(x + w - 0.24 - tw / 2, cy + 0.037, tag, 10,
                            C["text_secondary"], "600", BODY,
                            anchor="middle"))
        if i < len(items) - 1:
            out.append(line(x + 0.24, ry + rh, x + w - 0.24, ry + rh,
                            C["border"], sw=pt(0.75), opacity=0.6))
    if b.get("footer"):
        out.append(text(x + 0.24, y + h - 0.2, b["footer"], 10,
                        C["text_secondary"], "400", BODY))
    return "".join(out)


# ------------------------------------------------------------------ image
def png_size(p: Path):
    d = p.read_bytes()[:26]
    return struct.unpack(">II", d[16:24])


def b_image(b) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    path = ROOT / "projek_breast_cancer_R" / b["file"]
    out = []
    cap_h = 0.42
    if not path.exists():
        out.append(rect(x, y, w, h - cap_h, C["surface"], rx=0.1,
                        stroke=C["border"], sw=pt(1)))
        out.append(text(x + w / 2, y + (h - cap_h) / 2, "(gambar tidak ada)",
                        11, C["text_secondary"], anchor="middle"))
    else:
        pw, ph = png_size(path)
        iw, ih = w - 0.28, h - cap_h - 0.28
        ar = pw / ph
        dw, dh = (iw, iw / ar) if iw / ar <= ih else (ih * ar, ih)
        dx, dy = x + (w - dw) / 2, y + 0.14 + (ih - dh) / 2
        if b.get("frame", True):
            out.append(rect(x, y, w, h - cap_h, C["surface"], rx=0.1,
                            stroke=FRAME, sw=pt(1.2), shadow=True))
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        out.append(f'<image x="{u(dx):.2f}" y="{u(dy):.2f}" '
                   f'width="{u(dw):.2f}" height="{u(dh):.2f}" '
                   f'preserveAspectRatio="xMidYMid meet" '
                   f'xlink:href="data:image/png;base64,{b64}"/>')
    cap = wrap(b.get("caption", ""), u(w), pt(SCALE["caption"]))
    out.append(text_block(x, y + h - cap_h + 0.06, w, cap, SCALE["caption"],
                          C["text_secondary"]))
    return "".join(out)


# --------------------------------------------------------- teks & sampul
def b_text(b) -> str:
    st = b.get("style", {})
    size = st.get("size_pt", 13)
    fill = color(st.get("color", "text_primary"))
    weight = st.get("weight", "400")
    family = HEAD if weight in ("600", "700") else BODY
    lines = wrap(b["text"], u(b["w"]), pt(size), weight in ("600", "700"))
    lh = pt(size) * LH
    if b.get("role") == "title":
        lh = pt(size) * 1.18
    out = []
    y0 = u(b["y"]) + 0.8 * lh
    for i, ln in enumerate(lines):
        out.append(text(b["x"], y0 / U + i * lh / U, ln, size, fill, weight,
                        family, ls=st.get("letter_spacing")))
    return "".join(out)


def b_icon_badge_block(b) -> str:
    acc = color(b["accent"])
    return icon_badge(b["x"] + b["w"] / 2, b["y"] + b["h"] / 2,
                      min(b["w"], b["h"]), acc, b["icon"],
                      icon_ratio=0.56, fill_opacity=0.22)


DISPATCH = {
    "stat_card": b_stat_card,
    "icon_card": b_icon_card,
    "question_card": b_question_card,
    "callout": b_callout,
    "highlight_banner": b_highlight_banner,
    "table": b_table,
    "chart": b_chart,
    "process_flow": b_process_flow,
    "formula_flow": b_formula_flow,
    "ranked_list": b_ranked_list,
    "image": b_image,
    "text": b_text,
    "icon_badge": b_icon_badge_block,
}


# ================================================================= rakit
def build_slide(slide: dict) -> str:
    sid = slide["id"]
    body = []
    if slide.get("layout") == "cover":
        bg = slide["background"]
        body.append(f'<defs><linearGradient id="cov" x1="0" y1="0" x2="1" '
                    f'y2="1"><stop offset="0" stop-color="{bg["from"]}"/>'
                    f'<stop offset="1" stop-color="{bg["to"]}"/></linearGradient>'
                    f'</defs>')
        body.append(rect(0, 0, W / U, H / U, "url(#cov)"))
        body.append(f'<circle cx="{u(1.2):.0f}" cy="{u(0.6):.0f}" '
                    f'r="{u(2.8):.0f}" fill="{C["accent_benign"]}" '
                    f'fill-opacity="0.12"/>')
        body.append(f'<circle cx="{u(11.9):.0f}" cy="{u(6.4):.0f}" '
                    f'r="{u(3.4):.0f}" fill="{C["accent_malignant"]}" '
                    f'fill-opacity="0.12"/>')
    else:
        body.append(rect(0, 0, W / U, H / U, C["bg_light"]))
        m = SPEC["theme"]["master"]
        hd = m["header"]
        # judul dipastikan satu baris: kecilkan font bila perlu
        tsize = SCALE["slide_title"]
        while (text_w(slide["title"], pt(tsize), True) > u(hd["title_w"])
               and tsize > 24):
            tsize -= 0.5
        body.append(text(hd["title_x"], 0.78, slide["title"], tsize,
                         C["text_primary"], "700", HEAD))
        if slide.get("subtitle"):
            ssize = SCALE["slide_subtitle"]
            while (text_w(slide["subtitle"], pt(ssize)) > u(hd["title_w"])
                   and ssize > 12):
                ssize -= 0.5
            body.append(text(hd["title_x"], 1.06, slide["subtitle"], ssize,
                             C["text_secondary"], "400", BODY))
        un = hd["underline"]
        body.append(rect(un["x"], un["y"], un["w"], un["h"],
                         color(un["color"]), rx=0.03))

    for blk in slide["blocks"]:
        fn = DISPATCH.get(blk["type"])
        if fn:
            body.append(fn(blk))

    if slide.get("layout") != "cover":
        ft = SPEC["theme"]["master"]["footer"]
        body.append(text(0.6, 7.22, ft["left_text"], ft["font_size_pt"],
                         C[ft["color"]]))
        body.append(text(12.73, 7.22, str(sid), ft["font_size_pt"],
                         C[ft["color"]], "600", BODY, anchor="end"))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W:.2f}" height="{H:.2f}" viewBox="0 0 {W:.2f} {H:.2f}">'
            + "".join(body) + "</svg>")


def main():
    notes = ["# Speaker Notes\n"]
    for slide in SPEC["slides"]:
        out = ROOT / f"slide_{slide['id']}.svg"
        if slide.get("custom_svg") and out.exists():
            print(f"{out.name:14s} dilewati (custom_svg)")
        else:
            out.write_text(build_slide(slide), encoding="utf-8")
            print(f"{out.name:14s} ditulis")
        notes.append(f"## Slide {slide['id']}: {slide.get('title', '(cover)')}\n")
        notes.append(slide.get("speaker_notes", "-") + "\n")
    (ROOT / "speaker_notes.md").write_text("\n".join(notes), encoding="utf-8")
    print("speaker_notes.md ditulis")


if __name__ == "__main__":
    main()
