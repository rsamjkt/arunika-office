#!/usr/bin/env python3
"""Dokumen contoh (.docx, .xlsx, .pptx) untuk screenshot website: make-samples.py OUTDIR [SOFFICE]"""
import os, shutil, subprocess, sys, tempfile, time
import uno
from com.sun.star.beans import PropertyValue

OUT = os.path.abspath(sys.argv[1]); SOFFICE = sys.argv[2] if len(sys.argv) > 2 else "/usr/lib/libreoffice/program/soffice"

def pv(n, v):
    p = PropertyValue(); p.Name, p.Value = n, v; return p

prof = tempfile.mkdtemp(); pipe = f"arusmp{os.getpid()}"
proc = subprocess.Popen([SOFFICE, "--headless", "--norestore", "--nodefault", f"-env:UserInstallation=file://{prof}",
                         f"--accept=pipe,name={pipe};urp;"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
loc = uno.getComponentContext()
res = loc.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", loc)
for _ in range(60):
    try:
        ctx = res.resolve(f"uno:pipe,name={pipe};urp;StarOffice.ComponentContext"); break
    except Exception:
        time.sleep(0.5)
desk = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
os.makedirs(OUT, exist_ok=True)
tpl = os.path.expanduser("~/arunika-office/core/extras/source/templates/arunika")

def open_tpl(name):
    return desk.loadComponentFromURL(uno.systemPathToFileUrl(os.path.join(tpl, name)), "_blank", 0,
                                     (pv("Hidden", True), pv("AsTemplate", True)))

def save(doc, name, filt):
    doc.storeToURL(uno.systemPathToFileUrl(os.path.join(OUT, name)), (pv("FilterName", filt), pv("Overwrite", True)))
    doc.close(True)

# Dokumen
d = open_tpl("Normal.ott"); t = d.Text; c = t.createTextCursor()
def para(text, style):
    c.ParaStyleName = style; t.insertString(c, text, False); t.insertControlCharacter(c, 0, False)
para("Laporan Penjualan Triwulan III", "Title")
para("Tim Pemasaran · Oktober 2026", "Subtitle")
para("Ringkasan", "Heading 1")
para("Penjualan triwulan ketiga naik 12% dibanding triwulan sebelumnya. Kenaikan terbesar "
     "berasal dari wilayah Jawa Barat dan Jawa Timur, didorong oleh penjualan daring.", "Standard")
para("Capaian Utama", "Heading 2")
for s in ["Pesanan daring tumbuh 25%.",
          "Jumlah pelanggan baru bertambah 1.200 orang.",
          "Biaya pengiriman rata-rata turun 8%."]:
    para("•  " + s, "Standard")
para("Rencana Triwulan IV", "Heading 2")
para("Triwulan berikutnya difokuskan pada promosi akhir tahun dan perluasan jaringan mitra "
     "di luar Pulau Jawa.", "Standard")
save(d, "Laporan.docx", "MS Word 2007 XML")

# Lembar kerja
x = open_tpl("Book.ots"); sh = x.Sheets.getByIndex(0); sh.Name = "Penjualan"
rows = [["Wilayah", "Juli", "Agustus", "September", "Total", "Tren"],
        ["DKI Jakarta", 1240, 1385, 1502], ["Jawa Barat", 1610, 1702, 1788], ["Jawa Tengah", 812, 790, 845],
        ["Jawa Timur", 965, 1012, 1080], ["Bali", 540, 588, 612], ["Sumatra Utara", 433, 470, 498],
        ["Sulawesi Selatan", 702, 731, 760]]
for r, row in enumerate(rows):
    for col, v in enumerate(row):
        cell = sh.getCellByPosition(col, r)
        if isinstance(v, str): cell.String = v
        else: cell.Value = v
    if r:
        sh.getCellByPosition(4, r).Formula = f"=SUM(B{r+1}:D{r+1})"
        sh.getCellByPosition(5, r).Formula = f"=D{r+1}/B{r+1}-1"
n = len(rows) + 1
sh.getCellByPosition(0, n - 1).String = "Total"
for col in "BCDE":
    sh.getCellRangeByName(f"{col}{n}").Formula = f"=SUM({col}2:{col}{n-1})"
hdr = sh.getCellRangeByName("A1:F1"); hdr.CharWeight = 150; hdr.CellBackColor = 0x107C41; hdr.CharColor = 0xFFFFFF
tot = sh.getCellRangeByName(f"A{n}:F{n}"); tot.CharWeight = 150; tot.CellBackColor = 0xE2EFDA
nf = x.NumberFormats; loc_ = uno.createUnoStruct("com.sun.star.lang.Locale"); loc_.Language, loc_.Country = "en", "US"
def fmt(code):
    k = nf.queryKey(code, loc_, False)
    return k if k >= 0 else nf.addNew(code, loc_)
sh.getCellRangeByName(f"B2:E{n}").NumberFormat = fmt("#,##0")
sh.getCellRangeByName(f"F2:F{n}").NumberFormat = fmt("0.0%")
sh.Columns.getByIndex(0).Width = 3800
for i in range(1, 6): sh.Columns.getByIndex(i).Width = 2400
# bagan
rect = uno.createUnoStruct("com.sun.star.awt.Rectangle"); rect.X, rect.Y, rect.Width, rect.Height = 1000, 6200, 16000, 8000
addr = sh.getCellRangeByName(f"A1:D{n-1}").RangeAddress
sh.Charts.addNewByName("Penjualan", rect, (addr,), True, True)
x.storeToURL(uno.systemPathToFileUrl(os.path.join(OUT, "Penjualan.ods")), (pv("FilterName", "calc8"), pv("Overwrite", True)))
save(x, "Penjualan.xlsx", "Calc MS Excel 2007 XML")

# Presentasi
p = open_tpl("Blank.otp"); page = p.DrawPages.getByIndex(0); page.Layout = 0
shapes = [page.getByIndex(i) for i in range(page.Count)]
if shapes:
    shapes[0].String = "Rencana Kerja 2027"
if len(shapes) > 1:
    shapes[1].String = "Rapat Tim · Oktober 2026"
save(p, "Rapat.pptx", "Impress MS PowerPoint 2007 XML")
desk.terminate(); time.sleep(1); proc.kill(); shutil.rmtree(prof, ignore_errors=True)
print(sorted(os.listdir(OUT)))
