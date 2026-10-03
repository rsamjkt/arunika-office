#!/usr/bin/env python3
"""Bangun ulang ribbon Arunika Office dan terjemahan Indonesianya.

    python3 arunika/ribbon/generate.py [word|excel|powerpoint …]
"""
import importlib
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ribbon  # noqa: E402

APPS = ["word", "excel", "powerpoint"]
MODULE = {"sw": "swriter", "sc": "scalc", "sd": "simpress"}


def update_a11y_suppressions(ui_rel):
    """Ribbon berisi ratusan tombol ikon yang labelnya datang dari perintah UNO; gla11y menganggapnya
    fatal untuk berkas baru. Seperti notebookbar upstream, catat temuannya di berkas .suppr modul."""
    suppr = os.path.join(ribbon.ROOT, "solenv/sanitizers/ui/modules", MODULE[ui_rel.split("/")[0]] + ".suppr")
    with tempfile.TemporaryDirectory() as tmp:
        gen = os.path.join(tmp, "gen.suppr")
        subprocess.run([sys.executable, os.path.join(ribbon.ROOT, "bin/gla11y"), "-P", ribbon.ROOT + "/",
                        "-g", gen, "--widgets-suffixignored",
                        "+ValueSet,HBox,VBox,ToolBox,Preview,PreviewWin,PreviewWindow,PrevWindow",
                        "--widgets-button", "+svtlo-ManagedMenuButton", "-o", os.path.join(tmp, "out"), ui_rel],
                       cwd=ribbon.ROOT, capture_output=True)
        new = open(gen).read().splitlines() if os.path.exists(gen) else []
    old = [line for line in open(suppr).read().splitlines() if not line.startswith(ui_rel + ":")]
    with open(suppr, "w") as f:
        f.write("\n".join(old + new) + "\n")


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
        update_a11y_suppressions(spec.APP.out_ui)
        print(f"{name}: {os.path.relpath(path, ribbon.ROOT)} ({len(b.strings)} label)")
        for w in sorted(set(b.warnings)):
            print(f"  PERINGATAN: perintah tidak dikenal {w}")
            rc = 1
        for w in sorted(set(b.noicon)):
            print(f"  tanpa ikon: {w}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
