#!/usr/bin/env python3
"""Bangun ulang ribbon Arunika Office dan terjemahan Indonesianya.

    python3 arunika/ribbon/generate.py [word|excel|powerpoint …]
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ribbon  # noqa: E402

APPS = ["word", "excel", "powerpoint"]


def main(names):
    rc = 0
    for name in names or APPS:
        try:
            spec = importlib.import_module(name)
        except ModuleNotFoundError:
            print(f"lewati {name}: belum ada spesifikasi")
            continue
        b = ribbon.Builder(spec.APP)
        path = b.write()
        po = os.path.join(ribbon.ROOT, spec.APP.po)
        if os.path.exists(po):
            ribbon.write_po(po, spec.APP.out_ui, b.strings)
        print(f"{name}: {os.path.relpath(path, ribbon.ROOT)} ({len(b.strings)} label)")
        for w in sorted(set(b.warnings)):
            print(f"  PERINGATAN: perintah tidak dikenal {w}")
            rc = 1
        for w in sorted(set(b.noicon)):
            print(f"  tanpa ikon: {w}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
