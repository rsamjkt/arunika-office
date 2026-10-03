#!/usr/bin/env python3
"""Ikon aplikasi Arunika Office bergaya Fluent: pelat huruf berwarna di atas lembar dokumen.

    python3 arunika/icons/make-icons.py OUTDIR

Menulis OUTDIR/scalable/apps/arunika-<app>.svg dan PNG 16…512 bila rsvg-convert tersedia.
"""
import os
import shutil
import subprocess
import sys

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "out")
# app: (huruf, warna terang, warna utama, warna gelap, motif)
APPS = {
    "dokumen": ("D", "#41A5EE", "#2B7CD3", "#185ABD", "lines"),
    "lembar-kerja": ("L", "#33C481", "#21A366", "#107C41", "grid"),
    "presentasi": ("P", "#FF8F6B", "#ED6C47", "#C43E1C", "slide"),
    "gambar": ("G", "#B38BE8", "#8B5CD6", "#5B2DA3", "shapes"),
    "rumus": ("R", "#7A8CA3", "#5B6B82", "#3B4A5E", "lines"),
    "basis-data": ("B", "#E8749A", "#C7426F", "#93204A", "grid"),
    "office": ("A", "#FFC46B", "#F59A5B", "#D9508C", "lines"),
}


def motif(kind, c1, c2):
    if kind == "lines":
        return "".join(f'<rect x="58" y="{y}" width="{w}" height="6" rx="3" fill="{c2}" opacity=".9"/>'
                       for y, w in ((30, 46), (46, 46), (62, 46), (78, 46), (94, 32)))
    if kind == "grid":
        cells = []
        for r in range(5):
            for c in range(2):
                cells.append(f'<rect x="{60 + c * 24}" y="{28 + r * 16}" width="20" height="12" rx="2" '
                             f'fill="{c2 if (r + c) % 2 else c1}" opacity=".9"/>')
        return "".join(cells)
    if kind == "slide":
        return (f'<rect x="58" y="34" width="48" height="34" rx="4" fill="{c1}"/>'
                f'<rect x="58" y="78" width="48" height="6" rx="3" fill="{c2}"/>'
                f'<rect x="58" y="92" width="32" height="6" rx="3" fill="{c2}"/>')
    if kind == "shapes":
        return (f'<circle cx="74" cy="48" r="14" fill="{c1}"/>'
                f'<rect x="78" y="64" width="28" height="28" rx="4" fill="{c2}"/>')
    return ""


def svg(letter, light, main, dark, kind):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
<defs>
<linearGradient id="sheet" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#eef2f7"/></linearGradient>
<linearGradient id="plate" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{light}"/><stop offset=".55" stop-color="{main}"/><stop offset="1" stop-color="{dark}"/></linearGradient>
<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="2.5" flood-color="#000" flood-opacity=".28"/></filter>
</defs>
<rect x="40" y="12" width="78" height="104" rx="10" fill="url(#sheet)" stroke="{main}" stroke-opacity=".35" stroke-width="2" filter="url(#sh)"/>
{motif(kind, light, main)}
<rect x="10" y="34" width="60" height="60" rx="10" fill="url(#plate)" filter="url(#sh)"/>
<text x="40" y="78" text-anchor="middle" font-family="Inter, Segoe UI, Carlito, sans-serif" font-weight="700" font-size="42" fill="#ffffff">{letter}</text>
</svg>
'''


def main():
    sc = os.path.join(OUT, "scalable", "apps")
    os.makedirs(sc, exist_ok=True)
    rsvg = shutil.which("rsvg-convert")
    for app, spec in APPS.items():
        path = os.path.join(sc, f"arunika-{app}.svg")
        open(path, "w").write(svg(*spec))
        if rsvg:
            for size in (16, 24, 32, 48, 64, 128, 256, 512):
                d = os.path.join(OUT, f"{size}x{size}", "apps")
                os.makedirs(d, exist_ok=True)
                subprocess.run([rsvg, "-w", str(size), "-h", str(size), "-o",
                                os.path.join(d, f"arunika-{app}.png"), path], check=True)
    print("ikon →", OUT, "(png)" if rsvg else "(svg saja)")


if __name__ == "__main__":
    main()
