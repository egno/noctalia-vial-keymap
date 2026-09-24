# Vial Keymap

Shows the keymap of a Vial-configured split keyboard (splitkb Aurora Corne by default) as an
overlay, read from a Vial `.vil` export. All non-empty layers at once, with mod-taps, layer-taps,
combos, encoder bindings and the letters of your second OS layout (for example Russian). It is
the Linux port of [egno/vial_helper](https://github.com/egno/vial_helper).

![Vial Keymap overlay showing all layers of an Aurora Corne keymap](https://raw.githubusercontent.com/egno/noctalia-vial-keymap/main/docs/screenshot.png)

## Plugin

| Field | Value |
| --- | --- |
| ID | `egno/vial_keymap` |
| Entries | Bar widget: `icon`; panel: `keymap` |

## Requirements

- A `.vil` export of your keymap from [Vial](https://get.vial.today) (File → Save current layout). Default path: `~/aurora.vil`.
- `python3` and `libxkbcommon` (both standard on most systems) for the second-layout letters.
- Nothing else: the OS layouts are detected from the running compositor (Hyprland, niri, sway),
  `XKB_DEFAULT_LAYOUT` or `localectl`. On anything else set the layout in Settings.

## Usage

Toggle the overlay from your compositor keybind:

```sh
noctalia msg panel-toggle egno/vial_keymap:keymap
```

For example in Hyprland's Lua config:

```lua
hl.bind(mainMod .. " + K", hl.dsp.exec_cmd("noctalia msg panel-toggle egno/vial_keymap:keymap"))
```

Optionally add the bar widget `egno/vial_keymap:icon` (Settings → Bar, or in your config), a
keyboard glyph that toggles the overlay on click and opens the plugin settings on right or
middle click:

```toml
[widget.keymap]
type = "egno/vial_keymap:icon"
```

While the overlay is open: `0`–`9` zooms into a layer, `a` or `` ` `` shows all layers,
`←`/`→` cycle, `Esc` or a click outside closes. Clicking a layer card zooms into it. Layers
that contain only transparent or unassigned keys are hidden. The `.vil` is re-read on every
open and every 2 seconds while open, so a Vial re-export shows up immediately.

The overlay recognises the Aurora Corne / crkbd matrix (3×6+3 per half) and draws it with column
stagger and thumb clusters; other split boards get a mirrored grid, and non-split boards a plain
grid.

## Settings

Settings → Plugins → Vial Keymap:

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `vil_path` | `file` | `~/aurora.vil` | The Vial `.vil` export to display. |
| `layer_names` | `string` | *(empty)* | Comma-separated names in layer order, e.g. `Base, Nav, Sym, Fn`. Replaces `L1`-style legends on layer keys and in the layer chips. |
| `encoders` | `select` | `both` | Which half's encoder bindings to draw (`both`, `left`, `right`, `none`). Vial exports a slot per half even if unused. |
| `alt_layout` | `string` | *(empty)* | Second OS layout whose letters are drawn in the top-right corner of each cap, where they differ from the first layout. Empty auto-detects (see below); `none` turns the letters off; otherwise an XKB name such as `ru`, `rumac` or `de(neo)`. |

With `alt_layout` empty the plugin asks, in order, `hyprctl getoption input:kb_layout`,
`niri msg keyboard-layouts`, `swaymsg -t get_inputs`, the `XKB_DEFAULT_LAYOUT` environment variable
and `localectl status`, and takes the first two layouts it finds. With a single layout nothing is drawn.
niri and sway report display names ("Russian (phonetic)"), which are mapped back to XKB codes through
`evdev.xml` and the `name[Group1]` of any custom layout in `~/.config/xkb/symbols`.

## IPC

```sh
noctalia msg plugin egno/vial_keymap:keymap all layer 2   # zoom into layer 2
noctalia msg plugin egno/vial_keymap:keymap all all       # back to all layers
noctalia msg plugin egno/vial_keymap:keymap all reload    # re-read the .vil now
noctalia msg plugin egno/vial_keymap:keymap all layouts   # re-detect the OS layouts
noctalia msg plugin egno/vial_keymap:icon focused toggle  # same as clicking the bar icon
```

## Notes

- Reads only the configured `.vil` file. Writes nothing.
- Spawns the compositor's layout query (see Settings) and `python3 xkb_legends.py` (bundled)
  once per open, at most once a minute, to compute the second-layout letters. No network access.
- Macro keys are shown as `M0`, `M1`, … without their contents.
- Modifiers are drawn as Tabler icons (Ctrl `^`, Alt ⎇, Shift ⇧, Super ⌘). Change them in
  `M.MODS` at the top of `keycode.luau`.
- Tested on Hyprland with Noctalia 5.1.0. Layout detection for niri and sway follows their
  documented IPC output but has not been run on a live session; reports welcome.
- Source and issues: [github.com/egno/noctalia-vial-keymap](https://github.com/egno/noctalia-vial-keymap).
