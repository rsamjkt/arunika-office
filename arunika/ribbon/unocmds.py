"""Daftar perintah UNO (.uno:Xxx) beserta labelnya dari officecfg, untuk validasi spesifikasi ribbon."""
import os
import re
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UI = os.path.join(ROOT, "officecfg/registry/data/org/openoffice/Office/UI")
OOR = "{http://openoffice.org/2001/registry}"
FILES = {
    "generic": "GenericCommands.xcu",
    "writer": "WriterCommands.xcu",
    "calc": "CalcCommands.xcu",
    "impress": "DrawImpressCommands.xcu",
}


def load(kind):
    out = {}
    tree = ET.parse(os.path.join(UI, FILES[kind]))
    for node in tree.iter("node"):
        name = node.get(OOR + "name", "")
        if not name.startswith(".uno:"):
            continue
        props = {}
        for p in node.findall("prop"):
            v = p.find("value")
            if v is not None and v.text:
                props[p.get(OOR + "name")] = v.text
        out[name] = props
    return out


def commands(app):
    cmds = load("generic")
    cmds.update(load(app))
    return cmds


if __name__ == "__main__":
    import sys
    app = sys.argv[1] if len(sys.argv) > 1 else "writer"
    c = commands(app)
    pat = re.compile(sys.argv[2], re.I) if len(sys.argv) > 2 else None
    for k in sorted(c):
        lab = c[k].get("Label", "")
        if not pat or pat.search(k) or pat.search(lab):
            print(f"{k:45s} {lab!r:40s} ctx={c[k].get('ContextLabel','')!r} pop={c[k].get('PopupLabel','')!r}")
