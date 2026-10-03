#!/usr/bin/env python3
"""Gabungkan terjemahan tambahan Arunika (arunika/l10n/<lang>/<modul>.po) ke translations/source/<lang>/<modul>/messages.po.

Idempoten: blok lama di antara penanda diganti. Jalankan sebelum build (dipanggil oleh arunika/build.sh).
"""
import glob
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BEGIN, END = "# >>> arunika-l10n", "# <<< arunika-l10n"

for frag in sorted(glob.glob(os.path.join(ROOT, "arunika", "l10n", "*", "*.po"))):
    lang = os.path.basename(os.path.dirname(frag))
    module = os.path.splitext(os.path.basename(frag))[0]
    target = os.path.join(ROOT, "translations", "source", lang, module, "messages.po")
    if not os.path.exists(target):
        print(f"lewati {frag}: {target} tidak ada")
        continue
    text = open(target, encoding="utf-8").read()
    if BEGIN in text:
        head, rest = text.split(BEGIN, 1)
        text = head.rstrip("\n") + "\n" + rest.split(END, 1)[1].lstrip("\n")
    body = open(frag, encoding="utf-8").read().strip("\n")
    with open(target, "w", encoding="utf-8") as f:
        f.write(text.rstrip("\n") + f"\n\n{BEGIN}\n{body}\n{END}\n")
    print(f"{os.path.relpath(frag, ROOT)} → {os.path.relpath(target, ROOT)}")
