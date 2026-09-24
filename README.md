# Vial Keymap — Noctalia plugin

Linux port of [egno/vial_helper](https://github.com/egno/vial_helper) for the
[Noctalia](https://github.com/noctalia-dev/noctalia) desktop shell: shows the keymap of a
Vial-configured split keyboard (splitkb Aurora Corne by default) as an overlay, read from a
`.vil` export.

- All non-empty layers at once; `0`–`9` zooms into a layer, `a` or `` ` `` shows all, `←`/`→`
  cycle, `Esc` or a click outside closes. Clicking a layer card zooms into it.
- Mod-taps, layer-taps, combos and encoder bindings. Layer names from settings replace
  `L1`-style legends. Modifiers are drawn as Tabler icons (see `M.MODS` in `keycode.luau`).
- The letter of your **second OS layout** (e.g. Russian) in the top corner of each cap, taken
  from Hyprland's `input:kb_layout` and compiled with libxkbcommon, so custom layouts in
  `~/.config/xkb` work. Only drawn where it differs from the first layout.
- The `.vil` is re-read on every open and every 2 s while open, so a Vial re-export shows up
  immediately. Theme colours follow your Noctalia palette.

## Install

```sh
git clone https://github.com/egno/noctalia-vial-keymap ~/.local/share/noctalia/plugins/vial_keymap
noctalia msg plugins enable egno/vial_keymap
```

Then in `~/.config/noctalia/config.toml`:

```toml
[widget.keymap]                      # bar icon: click toggles, right-click opens settings
type = "egno/vial_keymap:icon"

[plugin_settings."egno/vial_keymap"]
vil_path    = "~/aurora.vil"
layer_names = "Base, Nav, Sym, Fn, Mou, Ext"
```

Add `"keymap"` to a bar's widget list (Settings → Bar, or `[bar.default] end = [...]`), and bind
a hotkey in your compositor, e.g. Hyprland's Lua config:

```lua
hl.bind(mainMod .. " + K", hl.dsp.exec_cmd("noctalia msg panel-toggle egno/vial_keymap:keymap"))
```

Requires `python3` and `libxkbcommon` (both standard) for the second-layout legends; without
`hyprctl` it falls back to a built-in ЙЦУКЕН table.

## Settings

Settings → Plugins → Vial Keymap: `.vil` path, comma-separated layer names, which half's
encoder to draw, and the second layout (auto from Hyprland, or an XKB name like `ru`,
`rumac`, `de(neo)`).

## Files

`plugin.toml` manifest · `panel.luau` overlay · `widget.luau` bar icon · `vil.luau` parser ·
`keycode.luau` keycode → label · `geometry.luau` key placement (Corne, generic split, grid) ·
`xkb_legends.py` OS layout legends.

## Development

Edit a `.luau` and Noctalia hot-reloads it. `noctalia plugins lint .` checks the manifest; the
log is `~/.cache/noctalia/noctalia.log`. IPC while open:

```sh
noctalia msg plugin egno/vial_keymap:keymap all layer 2   # zoom into layer 2
noctalia msg plugin egno/vial_keymap:keymap all all       # back to all layers
noctalia msg plugin egno/vial_keymap:keymap all reload    # re-read the .vil
noctalia msg plugin egno/vial_keymap:keymap all layouts   # re-detect OS layouts
```

Known Noctalia 5.1.0 issue: disabling the plugin while `widget.keymap` is still placed on a bar
segfaults the shell. Remove the widget from the bar first.

## License

[MIT](LICENSE)
