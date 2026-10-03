#!/usr/bin/env python3
"""Aset branding Arunika Office untuk --with-branding: splash, logo Start Center, banner About.

    python3 arunika/branding/make-branding.py OUTDIR
"""
import base64
import os
import sys

import cairo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
FONT = "Inter"
BLUE = (0x2B / 255, 0x57 / 255, 0x9A / 255)
INK = (0x24 / 255, 0x24 / 255, 0x24 / 255)
GREY = (0x61 / 255, 0x61 / 255, 0x61 / 255)
LOGO_B64 = base64.b64encode(open(os.path.join(HERE, "arunika-logo.svg"), "rb").read()).decode()


def logo_png(size):
    """Rasterkan logo SVG lewat librsvg (gi) bila ada, kalau tidak pakai PNG 256 px."""
    try:
        import gi
        gi.require_version("Rsvg", "2.0")
        from gi.repository import Rsvg
        h = Rsvg.Handle.new_from_file(os.path.join(HERE, "arunika-logo.svg"))
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        cr = cairo.Context(surf)
        vp = Rsvg.Rectangle()
        vp.x, vp.y, vp.width, vp.height = 0, 0, size, size
        h.render_document(cr, vp)
        return surf
    except Exception:
        src = cairo.ImageSurface.create_from_png(os.path.join(HERE, "arunika-logo-256.png"))
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        cr = cairo.Context(surf)
        cr.scale(size / src.get_width(), size / src.get_height())
        cr.set_source_surface(src, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BEST)
        cr.paint()
        return surf


def splash(w, h, name):
    s = h / 199
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    cr.set_source_rgb(*BLUE)          # pita warna khas Office di atas
    cr.rectangle(0, 0, w, 6 * s)
    cr.fill()
    lg = int(84 * s)
    cr.set_source_surface(logo_png(lg), 36 * s, (h - lg) / 2 - 8 * s)
    cr.paint()
    x = 36 * s + lg + 24 * s
    cr.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(38 * s)
    cr.set_source_rgb(*INK)
    cr.move_to(x, h / 2 - 2 * s)
    cr.show_text("Arunika")
    cr.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_source_rgb(*BLUE)
    cr.show_text(" Office")
    cr.set_font_size(14 * s)
    cr.set_source_rgb(*GREY)
    cr.move_to(x, h / 2 + 24 * s)
    cr.show_text("Dokumen · Lembar Kerja · Presentasi")
    surf.write_to_png(os.path.join(OUT, name))


def wordmark_svg(w, h, dark=False):
    ink = "#ffffff" if dark else "#242424"
    blue = "#8ab4f8" if dark else "#2B579A"
    lh = h * 0.86
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<image x="0" y="{(h - lh) / 2:.1f}" width="{lh:.1f}" height="{lh:.1f}" xlink:href="data:image/svg+xml;base64,{LOGO_B64}"/>
<text x="{lh + h * 0.25:.1f}" y="{h * 0.68:.1f}" font-family="{FONT}, Carlito, sans-serif" font-size="{h * 0.56:.1f}" fill="{ink}"><tspan font-weight="700">Arunika</tspan><tspan fill="{blue}"> Office</tspan></text>
</svg>
'''


def about_svg():
    w, h = 450, 120
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<rect width="{w}" height="{h}" fill="#ffffff"/>
<rect width="{w}" height="5" fill="#2B579A"/>
<image x="20" y="22" width="76" height="76" xlink:href="data:image/svg+xml;base64,{LOGO_B64}"/>
<text x="112" y="68" font-family="{FONT}, Carlito, sans-serif" font-size="34" fill="#242424"><tspan font-weight="700">Arunika</tspan><tspan fill="#2B579A"> Office</tspan></text>
<text x="113" y="92" font-family="{FONT}, Carlito, sans-serif" font-size="13" fill="#616161">Berbasis LibreOffice · untuk Arunika Linux</text>
</svg>
'''


os.makedirs(OUT, exist_ok=True)
splash(644, 199, "intro.png")
splash(990, 306, "intro-highres.png")
for name, (w, h, dark) in {"logo.svg": (300, 60, False), "logo_inverted.svg": (300, 60, True),
                           "logo-sc.svg": (300, 60, False), "logo-sc_inverted.svg": (300, 60, True)}.items():
    open(os.path.join(OUT, name), "w").write(wordmark_svg(w, h, dark))
open(os.path.join(OUT, "about.svg"), "w").write(about_svg())
open(os.path.join(OUT, "progress.conf"), "w").write(
    'PROGRESSBARCOLOR="43,87,154"\nPROGRESSSIZE="572,4"\nPROGRESSPOSITION="36,178"\n'
    'PROGRESSFRAMECOLOR="230,230,230"\nPROGRESSTEXTCOLOR="97,97,97"\nPROGRESSTEXTBASELINE="168"\n'
    'PROGRESSBARCOLOR_HIGHRES="43,87,154"\nPROGRESSSIZE_HIGHRES="880,6"\nPROGRESSPOSITION_HIGHRES="55,274"\n')
print("branding →", OUT)
