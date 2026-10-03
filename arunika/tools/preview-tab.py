#!/usr/bin/env python3
"""Pratinjau satu tab ribbon dengan LibreOffice sistem: tab itu dijadikan tab awal (context-default).

    preview-tab.py word|excel|powerpoint TABKEY OUT.png
"""
import copy
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ribbon"))
import ribbon  # noqa: E402
import gi  # noqa: E402
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402

name, key, out = sys.argv[1:4]
spec = __import__(name)
DEFAULT = {"default", "any", "Text", "DrawText"}
tabs = []
for t in spec.APP.tabs:
    if isinstance(t, ribbon.Tab):
        t = copy.copy(t)
        if t.key == key:
            t.contexts = sorted(DEFAULT | set(t.contexts))
        else:
            t.contexts = [c for c in t.contexts if c not in DEFAULT]
    tabs.append(t)
app = ribbon.App(spec.APP.name, spec.APP.module, spec.APP.src_ui, "/tmp/nb_preview.ui", None, tabs)
ribbon.Builder(app).write()
module = {"writer": "writer", "calc": "calc", "impress": "impress"}[spec.APP.module]
subprocess.run([os.path.join(HERE, "preview-system.sh"), module, "/tmp/nb_preview.ui", "/tmp/nb_full.png", os.environ.get("WAIT", "16")],
               check=True)
p = GdkPixbuf.Pixbuf.new_from_file("/tmp/nb_full.png")
p.new_subpixbuf(57, 48, 1486, 165).savev(out, "png", [], [])
