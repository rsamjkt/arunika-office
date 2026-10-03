#!/usr/bin/env python3
"""Templat bawaan Arunika Office dengan gaya Microsoft Office 365, dibuat lewat UNO (LibreOffice headless).

    python3 arunika/templates/make-templates.py OUTDIR [SOFFICE]

Hasil: Normal.ott (Word: Carlito 11, spasi setelah 8 pt, baris 1,08, margin 2,54 cm),
Book.ots (Excel: Carlito 11, kolom 64 px, baris 15 pt), Blank.otp (PowerPoint: tema putih, Carlito).
Carlito = font bebas yang ukuran hurufnya identik dengan Calibri, jadi tata letak dokumen .docx sama.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

import uno
from com.sun.star.beans import PropertyValue

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "out")
SOFFICE = sys.argv[2] if len(sys.argv) > 2 else "/usr/lib/libreoffice/program/soffice"
FONT, FONT_LIGHT = "Carlito", "Carlito"
HEADING = 0x2F5496       # biru judul Word
TEXT = 0x000000


def pv(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def cm(v):
    return int(round(v * 1000))   # 1/100 mm


def pt(v):
    return int(round(v * 2540 / 72))


def connect():
    prof = tempfile.mkdtemp(prefix="aru-tpl-")
    pipe = f"arutpl{os.getpid()}"
    proc = subprocess.Popen([SOFFICE, "--headless", "--norestore", "--nologo", "--nodefault",
                             f"-env:UserInstallation=file://{prof}",
                             f"--accept=pipe,name={pipe};urp;StarOffice.ComponentContext"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
    for _ in range(60):
        try:
            ctx = resolver.resolve(f"uno:pipe,name={pipe};urp;StarOffice.ComponentContext")
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.kill()
        raise SystemExit("soffice tidak bisa dihubungi")
    desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    return proc, prof, desktop


def new(desktop, kind):
    return desktop.loadComponentFromURL(f"private:factory/{kind}", "_blank", 0, (pv("Hidden", True),))


def save(doc, name, filt):
    url = uno.systemPathToFileUrl(os.path.join(OUT, name))
    doc.storeToURL(url, (pv("FilterName", filt), pv("Overwrite", True)))
    doc.close(True)


def set_font(props, name, size=None, color=None, bold=None):
    for suffix in ("", "Asian", "Complex"):
        props.setPropertyValue("CharFontName" + suffix, name)
        if size:
            props.setPropertyValue("CharHeight" + suffix, size)
    if color is not None:
        props.CharColor = color
    if bold is not None:
        props.CharWeight = 150.0 if bold else 100.0


def word(desktop):
    doc = new(desktop, "swriter")
    paras = doc.StyleFamilies.getByName("ParagraphStyles")
    std = paras.getByName("Standard")
    set_font(std, FONT, 11.0, TEXT)
    ls = std.ParaLineSpacing
    ls.Mode, ls.Height = 0, 108          # PROP 108 %
    std.ParaLineSpacing = ls
    std.ParaTopMargin, std.ParaBottomMargin = 0, pt(8)
    for name in ("Text body", "Body Text"):
        if paras.hasByName(name):
            body = paras.getByName(name)
            body.ParaTopMargin, body.ParaBottomMargin = 0, pt(8)
            ls = body.ParaLineSpacing
            ls.Mode, ls.Height = 0, 108
            body.ParaLineSpacing = ls
    head = {"Heading 1": (16, pt(12), 0), "Heading 2": (13, pt(2), 0), "Heading 3": (12, pt(2), 0)}
    if paras.hasByName("Heading"):
        set_font(paras.getByName("Heading"), FONT_LIGHT, None, HEADING, False)
    for name, (size, top, bottom) in head.items():
        if paras.hasByName(name):
            h = paras.getByName(name)
            set_font(h, FONT_LIGHT, float(size), HEADING if name != "Heading 3" else 0x1F3763, False)
            h.CharPosture = 0
            h.ParaTopMargin, h.ParaBottomMargin = top, bottom
    if paras.hasByName("Title"):
        t = paras.getByName("Title")
        set_font(t, FONT_LIGHT, 28.0, TEXT, False)
        t.ParaAdjust = 0
    if paras.hasByName("Subtitle"):
        st = paras.getByName("Subtitle")
        set_font(st, FONT, 11.0, 0x5A5A5A, False)
        st.ParaAdjust = 0
    for name in ("List", "Caption", "Index", "Table Contents", "Header", "Footer"):
        if paras.hasByName(name):
            set_font(paras.getByName(name), FONT, None)
    page = doc.StyleFamilies.getByName("PageStyles").getByName("Standard")
    page.Width, page.Height = cm(21.0), cm(29.7)
    for side in ("LeftMargin", "RightMargin", "TopMargin", "BottomMargin"):
        page.setPropertyValue(side, cm(2.54))
    save(doc, "Normal.ott", "writer8_template")


def excel(desktop):
    doc = new(desktop, "scalc")
    cells = doc.StyleFamilies.getByName("CellStyles")
    d = cells.getByName("Default")
    set_font(d, FONT, 11.0)
    for name in ("Heading", "Heading 1", "Heading 2"):
        if cells.hasByName(name):
            set_font(cells.getByName(name), FONT, None)
    sheets = doc.Sheets
    for i in range(sheets.Count):
        sh = sheets.getByIndex(i)
        cols = sh.Columns
        cols.Width = 1693          # 64 px (8,43 karakter) seperti Excel
        sh.Rows.Height = 529       # 15 pt
    if sheets.Count:
        sheets.getByIndex(0).Name = "Sheet1"
    save(doc, "Book.ots", "calc8_template")


def powerpoint(desktop):
    doc = new(desktop, "simpress")
    masters = doc.MasterPages
    for i in range(masters.Count):
        m = masters.getByIndex(i)
        bg = doc.createInstance("com.sun.star.drawing.Background")
        bg.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "SOLID")
        bg.FillColor = 0xFFFFFF
        m.Background = bg
        m.Width, m.Height = cm(33.867), cm(19.05)    # 16:9 "Layar lebar" PowerPoint
    styles = doc.StyleFamilies
    for fam_name in [styles.ElementNames[i] for i in range(len(styles.ElementNames))]:
        fam = styles.getByName(fam_name)
        for sname in fam.ElementNames:
            st = fam.getByName(sname)
            try:
                if sname == "title":
                    set_font(st, FONT_LIGHT, 44.0, TEXT, False)
                elif sname.startswith("outline"):
                    set_font(st, FONT, None, TEXT)
                elif sname in ("subtitle",):
                    set_font(st, FONT, 24.0, 0x595959)
                elif fam_name == "graphics" and sname in ("standard", "Default Drawing Style"):
                    set_font(st, FONT, 18.0)
            except Exception:
                pass
    pages = doc.DrawPages
    if pages.Count:
        pages.getByIndex(0).Layout = 0    # judul slide
    save(doc, "Blank.otp", "impress8_template")


def main():
    os.makedirs(OUT, exist_ok=True)
    proc, prof, desktop = connect()
    try:
        word(desktop)
        excel(desktop)
        powerpoint(desktop)
    finally:
        try:
            desktop.terminate()
        except Exception:
            pass
        time.sleep(1)
        proc.kill()
        shutil.rmtree(prof, ignore_errors=True)
    for f in sorted(os.listdir(OUT)):
        print(os.path.join(OUT, f), os.path.getsize(os.path.join(OUT, f)))


if __name__ == "__main__":
    main()
