#!/usr/bin/env python3
"""Berkas .desktop Arunika Office dari templat upstream (sysui/desktop/menus/*.desktop).

    python3 desktop.py OUTDIR
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MENUS = os.path.join(ROOT, "sysui", "desktop", "menus")
OUT = sys.argv[1]

# berkas upstream: (id, opsi soffice, Name, GenericName en, GenericName id, Comment en, Comment id)
APPS = [
    ("writer", "dokumen", "--writer", "Arunika Dokumen", "Word Processor", "Pengolah Kata",
     "Create and edit documents (.docx, .odt)", "Buat dan sunting dokumen (.docx, .odt)"),
    ("calc", "lembar-kerja", "--calc", "Arunika Lembar Kerja", "Spreadsheet", "Lembar Kerja",
     "Calculate, analyse and manage data (.xlsx, .ods)", "Hitung, analisis, dan kelola data (.xlsx, .ods)"),
    ("impress", "presentasi", "--impress", "Arunika Presentasi", "Presentation", "Presentasi",
     "Create and show slide presentations (.pptx, .odp)", "Buat dan tampilkan presentasi slide (.pptx, .odp)"),
    ("draw", "gambar", "--draw", "Arunika Gambar", "Drawing Program", "Program Gambar",
     "Diagrams, flowcharts and PDF editing", "Diagram, bagan alir, dan penyuntingan PDF"),
    ("math", "rumus", "--math", "Arunika Rumus", "Formula Editor", "Penyunting Rumus",
     "Create and edit mathematical formulas", "Buat dan sunting rumus matematika"),
    ("base", "basis-data", "--base", "Arunika Basis Data", "Database", "Basis Data",
     "Manage databases, queries and forms", "Kelola basis data, kueri, dan formulir"),
    ("startcenter", "office", "", "Arunika Office", "Office Suite", "Paket Perkantoran",
     "Documents, spreadsheets and presentations", "Dokumen, lembar kerja, dan presentasi"),
]


def field(text, key):
    m = re.search(rf"^{key}=(.*)$", text, re.M)
    return m.group(1) if m else ""


def main():
    os.makedirs(OUT, exist_ok=True)
    for src, app, opt, name, gen, gen_id, com, com_id in APPS:
        text = open(os.path.join(MENUS, f"{src}.desktop"), encoding="utf-8").read()
        mime = field(text, "MimeType")
        keys = field(text, "Keywords").replace("OpenOffice ", "").replace("LibreOffice ", "")
        cats = field(text, "Categories").replace("X-Red-Hat-Base;", "").replace("X-SuSE-Core-Office;", "")
        exe = f"arunika-{app}"
        lines = [
            "[Desktop Entry]",
            "Version=1.0",
            "Type=Application",
            f"Name={name}",
            f"GenericName={gen}",
            f"GenericName[id]={gen_id}",
            f"Comment={com}",
            f"Comment[id]={com_id}",
            f"Icon=arunika-{app}",
            f"Exec={exe} %U",
            f"TryExec={exe}",
            "Terminal=false",
            f"Categories={cats}",
            f"Keywords={keys}",
            f"MimeType={mime}",
            f"StartupWMClass=arunika-{app}",
            "StartupNotify=true",
            "InitialPreference=10",
            "X-KDE-Protocols=file,http,ftp,webdav,webdavs",
        ]
        if src == "startcenter":
            lines += ["Actions=Dokumen;LembarKerja;Presentasi;", "",
                      "[Desktop Action Dokumen]", "Name=New Document", "Name[id]=Dokumen Baru",
                      "Exec=arunika-dokumen", "",
                      "[Desktop Action LembarKerja]", "Name=New Workbook", "Name[id]=Buku Kerja Baru",
                      "Exec=arunika-lembar-kerja", "",
                      "[Desktop Action Presentasi]", "Name=New Presentation", "Name[id]=Presentasi Baru",
                      "Exec=arunika-presentasi"]
        else:
            lines += ["Actions=NewDocument;", "", "[Desktop Action NewDocument]",
                      "Name=New", "Name[id]=Baru", f"Exec={exe}"]
        path = os.path.join(OUT, f"arunika-{app}.desktop")
        open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print(path)


if __name__ == "__main__":
    main()
