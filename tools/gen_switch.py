#!/usr/bin/env python3
"""Writes plasma/desktoptheme/*/widgets/switch.svg (Halcyon Glass).

Look: flat pill track with a white pill knob inset 1.5px on every side.
  off = grey track with a faint 1px edge;  on = accent-coloured track (blue by default) with a slightly darker 1px outer edge.

Element contract (libplasma PlasmaComponents3/SwitchIndicator.qml, Plasma 6):
  hint-bar-size                       56x24 root (the QML insets the off track 1px each side)
  inactive-center                     off track (single piece, see track())
  active-center                       on track, shown from the left end to the right edge of the handle
  handle / handle-hover / handle-pressed   the knob. The QML clamps the handle flush to the 54px root while the track is
                                      1px inside it, so the inset is drawn INTO the handle as transparent padding:
                                      3.5px left/right (2px + 1.5px ring) and 1.5px top/bottom = an even 1.5px ring.
  handle-shadow, handle-focus         centred on the handle by the QML, so each is drawn centred in its own box.
  hint-stretch-borders                marker Breeze ships too.
(The previous version wrote groove-* / groove-highlight-*, which current libplasma does not read.)

Off track, on track (the accent / Highlight colour) and focus ring all follow the colour scheme.
Run:  python3 tools/gen_switch.py
"""
import re, pathlib

root = pathlib.Path(__file__).resolve().parent.parent / 'plasma/desktoptheme'

BAR_W, BAR_H = 56, 24          # root = visible track (52) + 2px each side that the QML trims/insets
TRACK_W = 52                   # visible track; spans x=2..54 of the 56px root
PAD_X, PAD_Y = 3.5, 1.5        # left/right: 2px root inset + 1.5px ring
PILL_W, PILL_H, PILL_W_DOWN = 31, 21, 35
HANDLE_W, HANDLE_H = PILL_W + 2 * PAD_X, BAR_H            # 36 x 24
HANDLE_W_DOWN = PILL_W_DOWN + 2 * PAD_X                   # 40 x 24
SHADOW_W, SHADOW_H = 40, 28
FOCUS_W, FOCUS_H = 40, 30

T = 'class="ColorScheme-Text" fill="currentColor"'
H = 'class="ColorScheme-Highlight" fill="currentColor"'
PALETTE = {
    'halcyon-glass-light': dict(
        off_fill=(T, 0.10), off_edge=('#000', 0.045),
        on_fill=(H, 1.0), on_edge=('#000', 0.18),
        knob='#ffffff', knob_down='#f1f1f2', shadow=(0.02, 0.035, 0.06), focus_opacity=0.65),
    'halcyon-glass-dark': dict(
        off_fill=(T, 0.15), off_edge=('#fff', 0.07),
        on_fill=(H, 1.0), on_edge=('#000', 0.20),
        knob='#ffffff', knob_down='#e4e4e6', shadow=(0.05, 0.08, 0.14), focus_opacity=0.75),
}

def g(i, x, y, w, h, body):
    return f'<g id="{i}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>{body}</g>'

def stadium(x, y, w, h):
    r = h / 2
    return f'M{x+r} {y} H{x+w-r} A{r} {r} 0 0 1 {x+w-r} {y+h} H{x+r} A{r} {r} 0 0 1 {x+r} {y} Z'

def fill_attrs(f):
    return f'{f[0]} fill-opacity="{f[1]}"' if isinstance(f, tuple) else f'fill="{f}"'

def track(prefix, y, fill, edge, item_w, x0):
    """One seamless piece (a 3-piece cap/middle/cap frame left a hairline seam at the joins on fractional display scales).
    libplasma lays the frames out like this (root = 56px):
        inactive: x 1..55  (54 wide)                          -> element 54 wide, visible track drawn from local x=1
        active:   x 2..handle.right-1 = 55 when on (53 wide)   -> element 53 wide, visible track drawn from local x=0
    so the visible track is x 2..54 in BOTH, i.e. the on/off tracks coincide at the left and right ends and the knob
    ring is the same on both sides. (Breeze's own 1px offset between the two is what used to leave a grey sliver at the left.)
    `active` is scaled horizontally while the knob slides."""
    ec, eo = edge
    return g(f'{prefix}-center', 0, y, item_w, BAR_H,
             f'<path d="{stadium(x0, y, TRACK_W, BAR_H)}" {fill_attrs(fill)}/>'
             f'<path d="{stadium(x0 + 0.5, y + 0.5, TRACK_W - 1, BAR_H - 1)}" fill="none" stroke="{ec}" stroke-opacity="{eo}"/>')

def handle(i, x, y, w, pill_w, colour):
    return g(i, x, y, w, HANDLE_H, f'<path d="{stadium(x+PAD_X, y+PAD_Y, pill_w, PILL_H)}" fill="{colour}"/>')

def shadow(x, y, ops):
    out, cx, cy = '', x + SHADOW_W / 2, y + SHADOW_H / 2
    for grow, o in zip((1.0, 0.5, 0), ops):
        w, h = PILL_W + 2 * grow, PILL_H + 2 * grow
        out += f'<path d="{stadium(cx-w/2, cy-h/2, w, h)}" fill="#000" fill-opacity="{o}"/>'
    return g('handle-shadow', x, y, SHADOW_W, SHADOW_H, out)

def focus(x, y, opacity):
    """1.5px accent ring hugging the knob (0.5px gap)."""
    cx, cy = x + FOCUS_W / 2, y + FOCUS_H / 2
    ow, oh = PILL_W + 4, PILL_H + 4
    iw, ih = ow - 3, oh - 3
    d = stadium(cx-ow/2, cy-oh/2, ow, oh) + ' ' + stadium(cx-iw/2, cy-ih/2, iw, ih)
    return g('handle-focus', x, y, FOCUS_W, FOCUS_H, f'<path {H} fill-opacity="{opacity}" fill-rule="evenodd" d="{d}"/>')

def build(p):
    return [
        g('hint-bar-size', 0, 60, BAR_W, BAR_H, ''),
        g('hint-stretch-borders', 0, 100, 1, 1, ''),
        track('inactive', 0, p['off_fill'], p['off_edge'], BAR_W - 2, 1),
        track('active', 30, p['on_fill'], p['on_edge'], BAR_W - 3, 0),
        handle('handle', 60, 0, HANDLE_W, PILL_W, p['knob']),
        handle('handle-hover', 60, 30, HANDLE_W, PILL_W, p['knob']),
        handle('handle-pressed', 60, 60, HANDLE_W_DOWN, PILL_W_DOWN, p['knob_down']),
        shadow(60, 90, p['shadow']),
        focus(110, 0, p['focus_opacity']),
    ]

def main():
    for theme in sorted(root.iterdir()):
        head = re.search(r'<defs>.*?</defs>', (theme / 'widgets/button.svg').read_text(), re.S).group(0)
        out = (f'<svg xmlns="http://www.w3.org/2000/svg" width="150" height="120" viewBox="0 0 150 120">{head}\n'
               + '\n'.join(build(PALETTE[theme.name])) + '\n</svg>\n')
        (theme / 'widgets/switch.svg').write_text(out)
        print('wrote', theme.name)

if __name__ == '__main__':
    main()
