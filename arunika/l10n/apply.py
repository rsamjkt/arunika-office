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

# Istilah: ganti kata di msgstr agar sama dengan Microsoft Office versi bahasa itu (mis. "Salindia" → "Slide")
for terms in sorted(glob.glob(os.path.join(ROOT, "arunika", "l10n", "terms-*.tsv"))):
    lang = os.path.basename(terms)[6:-4]
    pairs = [line.rstrip("\n").split("\t") for line in open(terms, encoding="utf-8")
             if line.strip() and not line.startswith("#")]
    changed = 0
    for po in glob.glob(os.path.join(ROOT, "translations", "source", lang, "**", "*.po"), recursive=True):
        if "/helpcontent2/" in po:
            continue
        lines = open(po, encoding="utf-8").read().split("\n")
        out, in_str = [], False
        for line in lines:
            if line.startswith("msgstr"):
                in_str = True
            elif not line.startswith('"'):
                in_str = False
            if in_str:
                for a, b in pairs:
                    line = line.replace(a, b)
            out.append(line)
        new = "\n".join(out)
        if new != "\n".join(lines):
            open(po, "w", encoding="utf-8").write(new)
            changed += 1
    print(f"{os.path.relpath(terms, ROOT)}: {changed} berkas .po diperbarui")
