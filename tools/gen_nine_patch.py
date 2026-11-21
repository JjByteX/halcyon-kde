#!/usr/bin/env python3
"""Generates the Plasma SVG nine-patches for listitem, viewitem and menubaritem (Halcyon Glass).

Why generated: the 5px corner slices of the old files could not carry the 12px row corners, and listitem had no
`selected` or `focus` state at all. Every state is written from one spec, so dark and light cannot drift apart again.
Run:  python3 gen_nine_patch.py <halcyon-global dir>
"""
import re, sys, pathlib
import radii

R = radii.ROW  # row corner (12px, 14px for a control). An exception to the tiers: see tools/radii.py
CELL = 2 * R + 1

HIGHLIGHT = ('ColorScheme-Highlight', 1.0)

def tile_rects(ox, oy):
    """(name, x, y, w, h) of the nine slices of one state block."""
    xs = [(0, R), (R, 1), (R + 1, R)]
    ys = [(0, R), (R, 1), (R + 1, R)]
    names = [['topleft', 'top', 'topright'], ['left', 'center', 'right'], ['bottomleft', 'bottom', 'bottomright']]
    out = []
    for j, (y, h) in enumerate(ys):
        for i, (x, w) in enumerate(xs):
            out.append((names[j][i], ox + x, oy + y, w, h))
    return out

def fmt(v):
    return ('%g' % v)

def corner_path(name, x, y, r):
    """Quarter disc (centre at the inside corner of the tile) for a corner slice, radius r, in a slice at x,y of size R."""
    if name == 'topleft':
        return f'M{fmt(x+R)} {fmt(y+R-r)} A{fmt(r)} {fmt(r)} 0 0 0 {fmt(x+R-r)} {fmt(y+R)} L{fmt(x+R)} {fmt(y+R)} Z'
    if name == 'topright':
        return f'M{fmt(x)} {fmt(y+R-r)} A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x+r)} {fmt(y+R)} L{fmt(x)} {fmt(y+R)} Z'
    if name == 'bottomleft':
        return f'M{fmt(x+R)} {fmt(y+r)} A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x+R-r)} {fmt(y)} L{fmt(x+R)} {fmt(y)} Z'
    if name == 'bottomright':
        return f'M{fmt(x)} {fmt(y+r)} A{fmt(r)} {fmt(r)} 0 0 0 {fmt(x+r)} {fmt(y)} L{fmt(x)} {fmt(y)} Z'
    raise ValueError(name)

def layer_svg(kind, name, x, y, w, h, cls, op, white=False):
    fill = '#fff' if white else 'currentColor'
    klass = '' if white else f' class="{cls}"'
    opa = f' fill-opacity="{fmt(op)}"' if op < 1 else ''
    if kind == 'fill':
        if name in ('topleft', 'topright', 'bottomleft', 'bottomright'):
            return f'<path fill="{fill}"{klass}{opa} d="{corner_path(name, x, y, R)}"/>'
        return f'<rect fill="{fill}"{klass}{opa} x="{x}" y="{y}" width="{w}" height="{h}"/>'
    # ring: 2px, drawn inside the edge
    t = 2
    if name == 'center':
        return ''
    if name in ('topleft', 'topright', 'bottomleft', 'bottomright'):
        d = corner_path(name, x, y, R) + ' ' + corner_path_inner(name, x, y)
        return f'<path fill="{fill}"{klass}{opa} fill-rule="evenodd" d="{d}"/>'
    rect = {'top': (x, y, w, t), 'bottom': (x, y + h - t, w, t), 'left': (x, y, t, h), 'right': (x + w - t, y, t, h)}[name]
    return f'<rect fill="{fill}"{klass}{opa} x="{rect[0]}" y="{rect[1]}" width="{rect[2]}" height="{rect[3]}"/>'

def corner_path_inner(name, x, y, t=2):
    r = R - t
    if name == 'topleft':
        return f'M{fmt(x+R)} {fmt(y+t)} A{r} {r} 0 0 0 {fmt(x+t)} {fmt(y+R)} L{fmt(x+R)} {fmt(y+R)} Z'
    if name == 'topright':
        return f'M{fmt(x)} {fmt(y+t)} A{r} {r} 0 0 1 {fmt(x+R-t)} {fmt(y+R)} L{fmt(x)} {fmt(y+R)} Z'
    if name == 'bottomleft':
        return f'M{fmt(x+R)} {fmt(y+R-t)} A{r} {r} 0 0 1 {fmt(x+t)} {fmt(y)} L{fmt(x+R)} {fmt(y)} Z'
    if name == 'bottomright':
        return f'M{fmt(x)} {fmt(y+R-t)} A{r} {r} 0 0 0 {fmt(x+R-t)} {fmt(y)} L{fmt(x)} {fmt(y)} Z'

def state_block(prefix, oy, layers, margins):
    """layers: list of (kind, class, opacity, white). margins: (left, top, right, bottom) content hints."""
    parts = []
    for name, x, y, w, h in tile_rects(0, oy):
        inner = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>'
        for kind, cls, op, white in layers:
            inner += layer_svg(kind, name, x, y, w, h, cls, op, white)
        parts.append(f'<g id="{prefix}-{name}">{inner}</g>')
    l, t, r, b = margins
    parts.append(f'<rect id="{prefix}-hint-left-margin" x="{CELL}" y="{oy}" width="{fmt(l)}" height="1" fill="#000" fill-opacity="0"/>')
    parts.append(f'<rect id="{prefix}-hint-top-margin" x="{CELL}" y="{oy}" width="1" height="{fmt(t)}" fill="#000" fill-opacity="0"/>')
    parts.append(f'<rect id="{prefix}-hint-right-margin" x="{CELL}" y="{oy}" width="{fmt(r)}" height="1" fill="#000" fill-opacity="0"/>')
    parts.append(f'<rect id="{prefix}-hint-bottom-margin" x="{CELL}" y="{oy}" width="1" height="{fmt(b)}" fill="#000" fill-opacity="0"/>')
    return '\n'.join(parts)

HOVER_ALPHA = 0.08   # surface-muted step: the same in dark and light (was 5% / 8.4%)
PRESS_ALPHA = 0.14   # one step darker
RING = ('ring', 'ColorScheme-Highlight', 0.85, False)

def spec(kind):
    """Per element: ordered (prefix, layers, margins). Margins are the content padding: 12px sides, 6px above and below."""
    pad = (12, 6, 12, 6)
    none = (0.01, 0.01, 0.01, 0.01)
    text = {'listitem': 'ColorScheme-ViewText', 'viewitem': 'ColorScheme-ViewText', 'menubaritem': 'ColorScheme-Text'}[kind]
    hover = [('fill', text, HOVER_ALPHA, False)]
    accent = [('fill',) + HIGHLIGHT + (False,)]
    accent_hover = accent + [('fill', '', 0.10, True)]
    if kind == 'listitem':
        return [
            ('normal', [], pad), ('section', [], pad), ('hover', hover, pad),
            ('pressed', accent, pad), ('selected', accent, pad), ('selected+hover', accent_hover, pad),
            ('focus', [RING], pad),
        ]
    if kind == 'viewitem':
        # a pure background behind a delegate that brings its own padding: no content margins
        return [
            ('normal', [], none), ('hover', hover, none), ('pressed', accent, none),
            ('selected', accent, none), ('selected+hover', accent_hover, none), ('focus', [RING], none),
        ]
    if kind == 'menubaritem':
        mp = (12, 8, 12, 8)
        return [('normal', [], mp), ('hover', hover, mp), ('pressed', [('fill', text, PRESS_ALPHA, False)], mp)]

def build(kind, defs):
    blocks, oy = [], 0
    for prefix, layers, margins in spec(kind):
        blocks.append(state_block(prefix, oy, layers, margins))
        oy += CELL + 4
    extra = ''  # no row separator: Halcyon draws no divider lines between list rows
    h = oy
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{CELL + 14}" height="{h}" viewBox="0 0 {CELL + 14} {h}">{defs}\n'
            + '\n'.join(blocks) + extra + '\n</svg>\n')

def main(root):
    root = pathlib.Path(root)
    for theme in ('halcyon-glass-dark', 'halcyon-glass-light'):
        for kind in ('listitem', 'viewitem', 'menubaritem'):
            path = root / 'plasma' / 'desktoptheme' / theme / 'widgets' / f'{kind}.svg'
            old = path.read_text()
            defs = re.search(r'<defs>.*?</defs>', old, re.S).group(0)  # keep each theme's colour block
            path.write_text(build(kind, defs))
            print('wrote', path.relative_to(root), f'{path.stat().st_size} bytes')

if __name__ == '__main__':
    main(sys.argv[1])
