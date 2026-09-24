#!/usr/bin/env python3
"""Print, as JSON, the character each QMK keycode produces under the given XKB layouts.

usage: xkb_legends.py <layouts> [<variants>]      e.g.  xkb_legends.py us,rumac  ,
       xkb_legends.py --names <name> [<name> ...] e.g.  xkb_legends.py --names "English (US)" Russian

The first form takes XKB layout / variant codes (what Hyprland, XKB_DEFAULT_LAYOUT and
localectl report). The second takes display names (what niri and sway report) and resolves
them through the XKB rules (evdev.xml) and the user's own symbols files in ~/.config/xkb.
Uses libxkbcommon through ctypes, so custom layouts in ~/.config/xkb are honoured.

Output, one legends table per input layout, in order (null where a layout did not compile):
  {"layouts": ["us", "rumac"], "variants": ["", ""], "legends": [{"KC_Q": "Q", ...}, {...}]}
"""
import ctypes, glob, json, os, re, sys
import xml.etree.ElementTree as ET

# QMK keycode aliases -> Linux evdev keycode (input-event-codes.h)
EVDEV = {
    ("KC_GRAVE", "KC_GRV"): 41,
    ("KC_1",): 2, ("KC_2",): 3, ("KC_3",): 4, ("KC_4",): 5, ("KC_5",): 6,
    ("KC_6",): 7, ("KC_7",): 8, ("KC_8",): 9, ("KC_9",): 10, ("KC_0",): 11,
    ("KC_MINUS", "KC_MINS"): 12, ("KC_EQUAL", "KC_EQL"): 13,
    ("KC_Q",): 16, ("KC_W",): 17, ("KC_E",): 18, ("KC_R",): 19, ("KC_T",): 20, ("KC_Y",): 21,
    ("KC_U",): 22, ("KC_I",): 23, ("KC_O",): 24, ("KC_P",): 25,
    ("KC_LBRACKET", "KC_LBRC"): 26, ("KC_RBRACKET", "KC_RBRC"): 27, ("KC_BSLASH", "KC_BSLS"): 43,
    ("KC_A",): 30, ("KC_S",): 31, ("KC_D",): 32, ("KC_F",): 33, ("KC_G",): 34, ("KC_H",): 35,
    ("KC_J",): 36, ("KC_K",): 37, ("KC_L",): 38, ("KC_SCOLON", "KC_SCLN"): 39, ("KC_QUOTE", "KC_QUOT"): 40,
    ("KC_Z",): 44, ("KC_X",): 45, ("KC_C",): 46, ("KC_V",): 47, ("KC_B",): 48, ("KC_N",): 49, ("KC_M",): 50,
    ("KC_COMMA", "KC_COMM"): 51, ("KC_DOT",): 52, ("KC_SLASH", "KC_SLSH"): 53,
    ("KC_NONUS_BSLASH", "KC_NUBS"): 86, ("KC_NONUS_HASH", "KC_NUHS"): 43,
}

XKB_USER_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "xkb")
XKB_SYSTEM_DIRS = ["/usr/share/X11/xkb", "/usr/share/xkeyboard-config-2", "/usr/local/share/X11/xkb", "/etc/xkb"]


class RuleNames(ctypes.Structure):
    _fields_ = [(n, ctypes.c_char_p) for n in ("rules", "model", "layout", "variant", "options")]


def rules_descriptions():
    """{description: (layout, variant)} from every evdev.xml we can find, user rules first."""
    out = {}
    for base in [XKB_USER_DIR] + XKB_SYSTEM_DIRS:
        path = os.path.join(base, "rules", "evdev.xml")
        if not os.path.isfile(path):
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for layout in root.iter("layout"):
            item = layout.find("configItem")
            name = item.findtext("name") if item is not None else None
            if not name:
                continue
            desc = item.findtext("description")
            if desc:
                out.setdefault(desc.strip(), (name, ""))
            for variant in layout.iter("variant"):
                vitem = variant.find("configItem")
                vname = vitem.findtext("name") if vitem is not None else None
                vdesc = vitem.findtext("description") if vitem is not None else None
                if vname and vdesc:
                    out.setdefault(vdesc.strip(), (name, vname))
    return out


def user_symbols_descriptions():
    """{description: (layout, variant)} from name[Group1] in ~/.config/xkb/symbols/*.

    Custom layouts usually ship without an evdev.xml, and compositors report them by the
    name[Group1] string of their symbols section.
    """
    out = {}
    block = re.compile(r'(default\s+)?(?:partial\s+)?(?:[\w]+\s+)*xkb_symbols\s+"([^"]+)"\s*\{(.*?)\};', re.S)
    for path in sorted(glob.glob(os.path.join(XKB_USER_DIR, "symbols", "*"))):
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        layout = os.path.basename(path)
        first = True
        for m in block.finditer(text):
            is_default, variant, body = bool(m.group(1)), m.group(2), m.group(3)
            n = re.search(r'name\[Group1\]\s*=\s*"([^"]*)"', body)
            if n:
                out.setdefault(n.group(1).strip(), (layout, "" if (is_default or first) else variant))
            first = False
    return out


def resolve_names(names):
    table = user_symbols_descriptions()
    for desc, code in rules_descriptions().items():
        table.setdefault(desc, code)
    layouts, variants = [], []
    for name in names:
        name = name.strip()
        if name in table:
            layout, variant = table[name]
        else:
            # Unknown description: maybe it already is a code such as "us" or "de(neo)".
            m = re.match(r"^([\w\-]+)\((.*)\)$", name)
            layout, variant = (m.group(1), m.group(2)) if m else (name, "")
        layouts.append(layout)
        variants.append(variant)
    return layouts, variants


def compile_legends(layouts, variants):
    lib = ctypes.CDLL("libxkbcommon.so.0")
    lib.xkb_context_new.restype = ctypes.c_void_p
    lib.xkb_keymap_new_from_names.restype = ctypes.c_void_p
    lib.xkb_keymap_new_from_names.argtypes = [ctypes.c_void_p, ctypes.POINTER(RuleNames), ctypes.c_int]
    lib.xkb_state_new.restype = ctypes.c_void_p
    lib.xkb_state_new.argtypes = [ctypes.c_void_p]
    lib.xkb_state_key_get_utf8.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_size_t]
    lib.xkb_state_unref.argtypes = [ctypes.c_void_p]
    lib.xkb_keymap_unref.argtypes = [ctypes.c_void_p]
    lib.xkb_context_unref.argtypes = [ctypes.c_void_p]

    ctx = lib.xkb_context_new(0)  # default flags: includes ~/.config/xkb
    result = []
    buf = ctypes.create_string_buffer(32)
    for layout, variant in zip(layouts, variants):
        names = RuleNames(None, None, layout.encode(), variant.encode() or None, None)
        km = lib.xkb_keymap_new_from_names(ctx, ctypes.byref(names), 0)
        if not km:
            result.append(None)
            continue
        st = lib.xkb_state_new(km)
        legends = {}
        for aliases, ev in EVDEV.items():
            n = lib.xkb_state_key_get_utf8(st, ev + 8, buf, 32)
            if n > 0:
                ch = buf.value.decode("utf-8", "replace")
                if ch.strip():
                    for a in aliases:
                        legends[a] = ch.upper()
        result.append(legends)
        lib.xkb_state_unref(st); lib.xkb_keymap_unref(km)
    lib.xkb_context_unref(ctx)
    return result


def main():
    args = sys.argv[1:]
    if args and args[0] == "--names":
        layouts, variants = resolve_names(args[1:] or ["us"])
    else:
        layouts = (args[0] if args else "us").split(",")
        variants = (args[1] if len(args) > 1 else "").split(",")
        variants += [""] * (len(layouts) - len(variants))
        variants = variants[: len(layouts)]
    out = {"layouts": layouts, "variants": variants, "legends": compile_legends(layouts, variants)}
    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
