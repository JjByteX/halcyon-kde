# Halcyon Glass (application style)

A Qt widget style forked from KDE Breeze 6.8.3. It follows the active Plasma style and colour scheme where they define
something, and falls back to stock Breeze for everything else.

What it changes: push/tool/combo/spin buttons, frames, line edits and group boxes get a thin glass edge with hover, pressed and
focus states. Menus, tooltips and alerts get rounded macOS-style surfaces. Sliders, dials, checkboxes, radio buttons and
scrollbars are restyled (overlay scrollbar with no arrows, widens on hover). Default buttons use the solid accent colour.

## Build

    cmake -B build -DCMAKE_INSTALL_PREFIX=~/.local -DCMAKE_BUILD_TYPE=Release
    cmake --build build -j && cmake --install build
    export QT_PLUGIN_PATH=~/.local/lib64/qt6/plugins   # may be lib/qt6/plugins
    kcmshell6 kcm_style                                # or: kate -style halcyonglass

Needs extra-cmake-modules, Qt 6.11 and KF6 6.30 (KColorScheme, KConfig, KGuiAddons, KIconThemes, KWindowSystem), plus
KF6FrameworkIntegration. The plugin is `halcyonglass6`, the style key is `HalcyonGlass`. It installs next to Breeze.

## Status

Not built against a full Qt 6.11 / KF6 setup yet. Only the drawing helpers were compiled (against Qt 6.4) and rendered for
`preview.png`. The rest, including the edits in `breezestyle.cpp`, is unbuilt, so check these first:

- default button label colour in icon mode
- row heights in Dolphin and System Settings
- menu window mask at the surface radius
- scrollbar size change in Dolphin and Kate, dragging off the bar, right-to-left layouts
- the QMessageBox light band sitting above the window background and under child widgets

Known gaps:

- Padding metrics are still Breeze's.
- No settings page. It reads Breeze's `breezerc`.
- Tooltip, menubar item and list/view selection styling is still mostly Breeze.
- Alert fills are opaque (Qt windows can't be translucent here), and dark alerts have no tuned fill.
- Dividers: toolbar/menubar/dialog hairlines, splitters, dock lines, status bar line, header separators, plain HLine/VLine frames, drop-down
  button dividers and list-row separators are not drawn. Menu item separators and the line under list headers stay. To bring one back,
  look for the `Halcyon Glass: no ...` comments in `breezestyle.cpp`.
- The scrollbar paints no track behind the pill on hover; the pill only widens.
- Overlay scrollbars don't hide when idle; Qt widgets have no signal for "scrolled recently".
- The `selected+hover` prefix in the Plasma item SVGs is a guess at what Plasma looks up.

## Layout notes

- Metrics and macOS 27 values live in `kstyle/breezemetrics.h` (`Tokens`). Control radius 6, surface radius 10, control height 36
  (change that one constant for 40). The radii are defined in `tools/radii.py`; run `python3 tools/radii.py --check` from the repo root
  after changing either side. `Frame_FrameRadius` stays 5 because tabs and headers use it as geometry.
- Icon sizes (`PM_SmallIconSize` and friends) use the larger of the style value and the system value.
- Plasma item and dialog SVGs are generated: `tools/gen_nine_patch.py`, `tools/gen_alert.py`,
  `tools/gen_switch.py`. Each takes the theme directory as its argument.
