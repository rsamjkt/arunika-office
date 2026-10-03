"""Generator ribbon Arunika Office: spesifikasi tab → grup → tombol ala Microsoft Office
menjadi berkas notebookbar (.ui, format Glade) yang dibaca VclBuilder LibreOffice.

Struktur hasil per tab:

    sfxlo-PriorityHBox "<Tab> Tab"            halaman tab (kontekstual lewat kelas context-*)
      sfxlo-DropdownBox (priority-N)          satu grup; menciut jadi tombol saat jendela sempit
        GtkBox vertikal
          GtkBox horizontal                   kolom-kolom grup (Big / Stack / Rows)
          GtkLabel                            nama grup di bawah, seperti Office
      GtkSeparator                            pemisah antargrup

Label tombol ditulis eksplisit (properti "label" yang bisa diterjemahkan, konteks Arunika<App>|<id>)
karena label perintah UNO bawaan LibreOffice berbeda dengan istilah Office.
"""
import copy
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unocmds  # noqa: E402

ROOT = unocmds.ROOT
ICONS = os.path.join(ROOT, "icon-themes", "colibre")


def _icon_links():
    links = {}
    try:
        for line in open(os.path.join(ICONS, "links.txt")):
            parts = line.split()
            if len(parts) == 2 and not line.startswith("#"):
                links[parts[0]] = parts[1]
    except OSError:
        pass
    return links


ICON_LINKS = _icon_links()


def has_icon(cmd, prefix):
    """Ada ikon Colibre untuk perintah? prefix: "cmd/32/" (32 px), "cmd/lc_" (24 px), "cmd/sc_" (16 px)."""
    name = cmd.split(":")[-1].split("?")[0].lower()
    for ext in (".png", ".svg"):
        rel = prefix + name + ext
        rel = ICON_LINKS.get(rel, rel)
        if os.path.exists(os.path.join(ICONS, rel)) or rel in ICON_LINKS:
            return True
    return False


# ---------------------------------------------------------------- spesifikasi
class Item:
    """Satu tombol. kind: big (ikon besar + label di bawah), small (ikon kecil + label di kanan),
    icon (ikon saja), widget (kontrol bawaan perintah: kotak font, galeri gaya, dll.)."""

    def __init__(self, kind, cmd, en=None, id_=None, drop=False, key=None, icon=None):
        self.kind, self.cmd, self.en, self.id_, self.drop, self.key = kind, cmd, en, id_, drop, key
        self.icon = icon    # nama ikon Colibre pengganti bila perintah tidak punya ikon (tanpa awalan/ekstensi)


def B(cmd, en, id_, drop=False, key=None, icon=None):
    return Item("big", cmd, en, id_, drop, key, icon)


def S(cmd, en, id_, drop=False, key=None, icon=None):
    return Item("small", cmd, en, id_, drop, key, icon)


def I(cmd, drop=False, icon=None):  # noqa: E743
    return Item("icon", cmd, drop=drop, icon=icon)


# lebar kontrol bawaan seperti di Office (px); None = ukuran bawaan LibreOffice
WIDGET_WIDTH = {}  # width-request memotong panah dropdown kombo; pakai ukuran bawaan


def W(cmd, width=None):
    it = Item("widget", cmd)
    it.width = width or WIDGET_WIDTH.get(cmd)
    return it


class Stack:
    """Kolom berisi tombol kecil bertumpuk (maks. 3), seperti Potong/Salin/Pewarna Format."""

    def __init__(self, *items):
        self.items = items


class Rows:
    """Kolom berisi baris-baris toolbar ikon (mis. grup Font: baris kotak font, baris B I U)."""

    def __init__(self, *rows, expand=False):
        self.rows, self.expand = rows, expand


class Group:
    def __init__(self, key, en, id_, *columns, priority=None):
        self.key, self.en, self.id_, self.columns, self.priority = key, en, id_, columns, priority


class Tab:
    def __init__(self, key, en, id_, *groups, contexts=None, accel=None):
        self.key, self.en, self.id_, self.groups = key, en, id_, groups
        self.contexts = contexts or []
        self.accel = accel


class CopyTab:
    """Tab kontekstual yang diambil dari notebookbar.ui bawaan LibreOffice (Tabel, Gambar, Bentuk, …)
    dengan nama tab diganti istilah Office."""

    def __init__(self, page_id, label_id, en, id_, key):
        self.page_id, self.label_id, self.en, self.id_, self.key = page_id, label_id, en, id_, key


class App:
    def __init__(self, name, module, src_ui, out_ui, po, tabs):
        self.name, self.module, self.src_ui, self.out_ui, self.po, self.tabs = name, module, src_ui, out_ui, po, tabs


# ---------------------------------------------------------------- pembangun XML
class Builder:
    def __init__(self, app):
        self.app = app
        self.ctx = f"Arunika{app.name}"
        self.strings = []           # (msgctxt, msgid, msgstr)
        self.ids = set()
        self.cmds = unocmds.commands(app.module)
        self.warnings = []
        self.noicon = []

    # -- utilitas
    def uid(self, base):
        base = "aru" + "".join(ch for ch in base if ch.isalnum())
        n, i = base, 1
        while n in self.ids:
            i += 1
            n = f"{base}{i}"
        self.ids.add(n)
        return n

    @staticmethod
    def prop(el, name, value, **attrs):
        p = ET.SubElement(el, "property", name=name, **attrs)
        p.text = value
        return p

    def tr(self, el, name, key, en, id_):
        ctx = f"{self.ctx}|{key}"
        self.prop(el, name, en, translatable="yes", context=ctx)
        self.strings.append((ctx, en, id_))

    def obj(self, parent, cls, id_=None, child_type=None):
        ch = ET.SubElement(parent, "child", **({"type": child_type} if child_type else {}))
        o = ET.SubElement(ch, "object", **{"class": cls, **({"id": id_} if id_ else {})})
        return ch, o

    def packing(self, ch, **kw):
        pk = ET.SubElement(ch, "packing")
        for k, v in kw.items():
            self.prop(pk, k.replace("_", "-"), v)

    def base(self, o, focus=False):
        self.prop(o, "visible", "True")
        self.prop(o, "can-focus", "True" if focus else "False")

    def check(self, cmd):
        if cmd.startswith(".uno:") and cmd.split("?")[0] not in self.cmds:
            self.warnings.append(cmd)

    # -- toolbar
    def toolbox(self, parent, items, style, large=False, valign="center", hexpand=False):
        ch, tb = self.obj(parent, "sfxlo-NotebookbarToolBox", self.uid("tb" + items[0].cmd.split(":")[-1]))
        self.base(tb)
        self.prop(tb, "valign", valign)
        if hexpand:
            self.prop(tb, "hexpand", "True")
        self.prop(tb, "toolbar-style", style)
        self.prop(tb, "show-arrow", "False")
        big32 = large and all(has_icon(i.icon or i.cmd, "cmd/32/") for i in items)
        if large:   # ikon 32 px seperti tombol besar Office, kalau tidak ada pakai 24 px
            self.prop(tb, "icon_size", "5" if big32 else "3")
        for it in items:
            self.check(it.cmd)
            if it.kind != "widget" and not it.icon and it.cmd.startswith(".uno:") and not (
                    has_icon(it.cmd, "cmd/sc_") or has_icon(it.cmd, "cmd/lc_")):
                self.noicon.append(it.cmd)
            cls = "GtkMenuToolButton" if it.drop else "GtkToolButton"
            ich, btn = self.obj(tb, cls, self.uid("btn" + it.cmd.split(":")[-1].split("?")[0]))
            self.base(btn)
            self.prop(btn, "action-name", it.cmd)
            if getattr(it, "width", None):
                self.prop(btn, "width-request", str(it.width))
            if it.icon:
                prefix = "cmd/32/" if big32 else ("cmd/lc_" if large else "cmd/sc_")
                self.prop(btn, "icon-name", f"{prefix}{it.icon}.png")
            if it.en:
                self.tr(btn, "label", it.key or ("btn" + it.cmd.split(":")[-1].split("?")[0].split(".")[-1]),
                        it.en, it.id_)
            self.packing(ich, expand="False", homogeneous="False")
        return ch

    def box(self, parent, vertical, id_base, spacing=0, valign=None, hexpand=False):
        ch, b = self.obj(parent, "GtkBox", self.uid(id_base))
        self.base(b)
        if vertical:
            self.prop(b, "orientation", "vertical")
        if spacing:
            self.prop(b, "spacing", str(spacing))
        if valign:
            self.prop(b, "valign", valign)
        if hexpand:
            self.prop(b, "hexpand", "True")
        return ch, b

    def column(self, parent, col, pos):
        if isinstance(col, Item):
            ch = self.toolbox(parent, [col], "both" if col.kind == "big" else
                              ("both-horiz" if col.kind == "small" else "icons"),
                              large=col.kind == "big", valign="fill" if col.kind == "big" else "center",
                              hexpand=col.kind == "widget")
        elif isinstance(col, Stack):
            ch, b = self.box(parent, True, "stack", spacing=1, valign="center")
            for i, it in enumerate(col.items):
                c = self.toolbox(b, [it], "both-horiz" if it.kind == "small" else "icons")
                self.packing(c, expand="False", fill="True", position=str(i))
        elif isinstance(col, Rows):
            ch, b = self.box(parent, True, "rows", spacing=2, valign="center", hexpand=col.expand)
            for i, row in enumerate(col.rows):
                c = self.toolbox(b, list(row), "icons", hexpand=col.expand)
                self.packing(c, expand="False", fill="True", position=str(i))
        else:
            raise TypeError(col)
        self.packing(ch, expand="True" if getattr(col, "expand", False) or
                     (isinstance(col, Item) and col.kind == "widget") else "False",
                     fill="True", position=str(pos))

    def group(self, parent, tab, g, pos, last):
        if g.priority is not None:
            ch, dd = self.obj(parent, "sfxlo-DropdownBox", self.uid(f"dd{tab.key}{g.key}"))
            self.base(dd)
            self.tr(dd, "tooltip-text", f"{tab.key}{g.key}Group", g.en, g.id_)
            holder = dd
        else:
            ch, holder = None, parent
        gch, gb = self.box(holder, True, f"g{tab.key}{g.key}")
        self.prop(gb, "margin-start", "4")
        self.prop(gb, "margin-end", "4")
        cch, cb = self.box(gb, False, f"c{tab.key}{g.key}", spacing=2)
        self.prop(cb, "vexpand", "True")
        for i, col in enumerate(g.columns):
            self.column(cb, col, i)
        self.packing(cch, expand="True", fill="True", position="0")
        lch, lab = self.obj(gb, "GtkLabel", self.uid(f"lb{tab.key}{g.key}"))
        self.base(lab)
        self.prop(lab, "halign", "center")
        self.prop(lab, "valign", "end")
        self.tr(lab, "label", f"lb{tab.key}{g.key}", g.en, g.id_)
        attrs = ET.SubElement(lab, "attributes")
        ET.SubElement(attrs, "attribute", name="scale", value="0.85")
        self.packing(lch, expand="False", fill="True", position="1")
        if ch is not None:
            self.packing(gch, expand="False", fill="True", position="0")
            # <style> must follow the children: VclBuilder creates the widget at its first <child>
            # and drops a priority class seen before that
            style = ET.SubElement(holder, "style")
            ET.SubElement(style, "class", name=f"priority-{g.priority}")
            self.packing(ch, expand="False", fill="True", position=str(pos * 2))
        else:
            self.packing(gch, expand="False", fill="True", position=str(pos * 2))
        if not last:
            sch, sep = self.obj(parent, "GtkSeparator", self.uid(f"sep{tab.key}{g.key}"))
            self.base(sep)
            self.prop(sep, "orientation", "vertical")
            self.prop(sep, "margin-top", "6")
            self.prop(sep, "margin-bottom", "6")
            self.packing(sch, expand="False", fill="True", position=str(pos * 2 + 1))

    def tab(self, tabctl, tab, pos):
        ch, page = self.obj(tabctl, "sfxlo-PriorityHBox", f"{tab.key} Tab")
        self.ids.add(f"{tab.key} Tab")
        self.base(page)
        self.prop(page, "valign", "fill")
        self.prop(page, "vexpand", "True")
        self.prop(page, "spacing", "2")
        for i, g in enumerate(tab.groups):
            self.group(page, tab, g, i, i == len(tab.groups) - 1)
        self.packing(ch, position=str(pos))
        tch, lab = self.obj(tabctl, "GtkLabel", self.uid(f"{tab.key}Label"), child_type="tab")
        self.base(lab)
        en = tab.en if not tab.accel else tab.en.replace(tab.accel, "~" + tab.accel, 1)
        self.tr(lab, "label", f"{tab.key}TabLabel", en, tab.id_)
        self.prop(lab, "use-underline", "True")
        if tab.contexts:
            st = ET.SubElement(lab, "style")
            for c in tab.contexts:
                ET.SubElement(st, "class", name=f"context-{c}")
        self.packing(tch, position=str(pos), tab_fill="False")

    # -- tab salinan dari notebookbar bawaan
    def copy_tab(self, tabctl, src_ctl, ct, pos):
        page_ch = tab_ch = None
        children = src_ctl.findall("child")
        for i, c in enumerate(children):
            o = c.find("object")
            if o is not None and o.get("id") == ct.page_id:
                page_ch, tab_ch = c, children[i + 1]
        if page_ch is None:
            raise SystemExit(f"tab {ct.page_id} tidak ada di {self.app.src_ui}")
        page_ch, tab_ch = copy.deepcopy(page_ch), copy.deepcopy(tab_ch)
        for o in page_ch.iter("object"):
            if o.get("id"):
                self.ids.add(o.get("id"))
        for c in (page_ch, tab_ch):
            pk = c.find("packing")
            if pk is not None:
                for p in pk.findall("property"):
                    if p.get("name") == "position":
                        p.text = str(pos)
        lab = tab_ch.find("object")
        for p in lab.findall("property"):
            if p.get("name") == "label":
                ctx = f"{self.ctx}|{ct.key}TabLabel"
                p.set("context", ctx)
                p.text = ct.en
                self.strings.append((ctx, ct.en, ct.id_))
        tabctl.append(page_ch)
        tabctl.append(tab_ch)

    # -- dokumen lengkap
    def build(self):
        src = ET.parse(os.path.join(ROOT, self.app.src_ui)).getroot()
        out = ET.Element("interface", domain=src.get("domain", ""))
        req = src.find("requires")
        if req is not None:
            out.append(copy.deepcopy(req))
        for o in src.findall("object"):       # menu-menu yang dipakai tab salinan
            if o.get("class") == "GtkMenu":
                out.append(copy.deepcopy(o))
                for d in o.iter("object"):
                    if d.get("id"):
                        self.ids.add(d.get("id"))
        src_ctl = next(o for o in src.iter("object") if o.get("class") == "sfxlo-NotebookbarTabControl")

        nb = ET.SubElement(out, "object", **{"class": "GtkGrid", "id": "NotebookBar"})
        self.base(nb)
        self.prop(nb, "hexpand", "True")
        bch, bx = self.obj(nb, "GtkBox", "box")
        self.base(bx)
        self.prop(bx, "hexpand", "True")
        self.prop(bx, "orientation", "vertical")
        cch, ctl = self.obj(bx, "sfxlo-NotebookbarTabControl", "ContextContainer")
        self.base(ctl, focus=True)
        self.prop(ctl, "hexpand", "True")
        for pos, t in enumerate(self.app.tabs):
            if isinstance(t, CopyTab):
                self.copy_tab(ctl, src_ctl, t, pos)
            else:
                self.tab(ctl, t, pos)
        self.packing(cch, expand="False", fill="True", position="0")
        self.packing(bch, left_attach="0", top_attach="0")
        ET.indent(out, space="  ")
        return out

    def write(self):
        tree = self.build()
        path = os.path.join(ROOT, self.app.out_ui)
        with open(path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write("<!-- Dibuat oleh arunika/ribbon/generate.py — jangan diubah langsung. -->\n")
            f.write(ET.tostring(tree, encoding="unicode"))
            f.write("\n")
        return path


# ---------------------------------------------------------------- terjemahan
PO_BEGIN = "# >>> arunika-ribbon"
PO_END = "# <<< arunika-ribbon"


def po_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def write_po(po_path, src_ui, strings):
    """Sisipkan/ganti blok terjemahan Indonesia untuk label ribbon di messages.po modul."""
    text = open(po_path, encoding="utf-8").read()
    if PO_BEGIN in text:
        head, rest = text.split(PO_BEGIN, 1)
        text = head.rstrip("\n") + "\n" + rest.split(PO_END, 1)[1].lstrip("\n")
    seen, lines = set(), [PO_BEGIN]
    for ctx, en, id_ in strings:
        if (ctx, en) in seen or not id_:
            continue
        seen.add((ctx, en))
        lines += ["", f"#: {src_ui}", f'msgctxt "{po_escape(ctx)}"', f'msgid "{po_escape(en)}"',
                  f'msgstr "{po_escape(id_)}"']
    lines += ["", PO_END, ""]
    with open(po_path, "w", encoding="utf-8") as f:
        f.write(text.rstrip("\n") + "\n\n" + "\n".join(lines))
