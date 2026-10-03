#!/usr/bin/env python3
"""Screenshot layar X (mis. Xvfb) ke PNG: DISPLAY=:78 shot.py OUT.png [x y w h]"""
import sys

import gi
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk  # noqa: E402

root = Gdk.get_default_root_window()
x, y, w, h = (int(v) for v in sys.argv[2:6]) if len(sys.argv) >= 6 else (0, 0, root.get_width(), root.get_height())
Gdk.pixbuf_get_from_window(root, x, y, w, h).savev(sys.argv[1], "png", [], [])
