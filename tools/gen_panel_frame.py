#!/usr/bin/env python3
"""Rebuilds the corner art of the dock and tooltip frames for the radii in tools/radii.py.

    python3 tools/gen_panel_frame.py [--root DIR] [--check]       run from the repo root

Owns, in both Plasma styles:
    widgets/panel-background.svg   radius radii.DOCK   (the dock / panel)
    widgets/tooltip.svg            radius radii.LABEL  (tooltips and dock labels)

What it rewrites in each file: the 9 body tiles (corner, edge and centre pieces, with the dark theme's 1px outline and
highlight rings), the 9 blur-mask tiles, and the content-margin hints. Cells are radius + 2 px, like dialogs/background.svg.
The shadow art, colours and everything else are left as they are. The body is laid out to the right of the shadow sheet and
the mask hints sit right of the mask, so nothing overlaps whatever the radius is. Re-running changes nothing.

Run tools/gen_panel_variants.py afterwards: it copies these files into opaque/ and translucent/.
--check writes nothing and exits 1 if a file is not what the current radii would produce.

Not owned: widgets/background.svg (the light one has extra hairline shapes inside its tiles) and dialogs/background.svg
(tools/gen_alert.py + tools/gen_popup_shadow.py).
"""
import argparse, math, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import radii

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parent.parent / 'plasma/desktoptheme'
THEMES = ('halcyon-glass-dark', 'halcyon-glass-light')
OWNED = (('widgets/panel-background.svg', radii.DOCK), ('widgets/tooltip.svg', radii.LABEL))
ORDER = ['topleft', 'top', 'topright', 'left', 'center', 'right', 'bottomleft', 'bottom', 'bottomright']
HEADER = re.compile(r'<svg xmlns="http://www.w3.org/2000/svg" width="(\d+)" height="(\d+)" viewBox="0 0 \d+ \d+">')


def body(R, ring, bx):
    """Body tiles of the frame: cell C = R + 2, laid out as a 3x3 sheet whose left edge is bx. ring = dark outline + highlight."""
    C = R + 2

    def corner(name):
        ox = bx if 'left' in name else bx + C + 1
        oy = 0 if 'top' in name else C + 1

        def shape(i):   # i = inset: 0 outer edge, 1 inside the outline, 2 inside the highlight
            r = R - i
            if name == 'topleft':     return f'M{ox+C} {oy+i} L{ox+R} {oy+i} A{r} {r} 0 0 0 {ox+i} {oy+R} L{ox+i} {oy+C} L{ox+C} {oy+C} Z'
            if name == 'topright':    return f'M{ox} {oy+i} L{ox+2} {oy+i} A{r} {r} 0 0 1 {ox+C-i} {oy+R} L{ox+C-i} {oy+C} L{ox} {oy+C} Z'
            if name == 'bottomleft':  return f'M{ox+C} {oy+C-i} L{ox+R} {oy+C-i} A{r} {r} 0 0 1 {ox+i} {oy+2} L{ox+i} {oy} L{ox+C} {oy} Z'
            if name == 'bottomright': return f'M{ox} {oy+C-i} L{ox+2} {oy+C-i} A{r} {r} 0 0 0 {ox+C-i} {oy+2} L{ox+C-i} {oy} L{ox} {oy} Z'
        return ox, oy, shape

    out = {}
    for name in ('topleft', 'topright', 'bottomleft', 'bottomright'):
        ox, oy, shape = corner(name)
        g = f'<rect x="{ox}" y="{oy}" width="{C}" height="{C}" fill="#000" fill-opacity="0"/>'
        g += f'<path d="{shape(0)}" fill="currentColor" class="ColorScheme-Background"/>'
        if ring:
            hl = 'hl-top' if 'top' in name else 'hl-bottom'
            g += f'<path fill="#000000" fill-opacity="0.2" fill-rule="evenodd" d="{shape(0)} {shape(1)}"/>'
            g += f'<path fill="url(#{hl})" fill-rule="evenodd" d="{shape(1)} {shape(2)}"/>'
        out[name] = g

    def edge(name, x, y, w, h):
        g = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>'
        g += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="currentColor" class="ColorScheme-Background"/>'
        if ring:
            dot = lambda xx, yy, fill, op: f'<rect x="{xx}" y="{yy}" width="1" height="1" fill="{fill}" fill-opacity="{op}"/>'
            if name == 'top':    g += dot(x, y, '#000000', 0.2) + dot(x, y + 1, '#ffffff', 0.12)
            if name == 'bottom': g += dot(x, y + h - 1, '#000000', 0.2) + dot(x, y + h - 2, '#ffffff', 0.12)
            if name == 'left':   g += dot(x, y, '#000000', 0.2) + dot(x + 1, y, '#ffffff', 0.05)
            if name == 'right':  g += dot(x + w - 1, y, '#000000', 0.2) + dot(x + w - 2, y, '#ffffff', 0.05)
        return g

    out['top'] = edge('top', bx + C, 0, 1, C)
    out['left'] = edge('left', bx, C, C, 1)
    out['center'] = (f'<rect x="{bx+C}" y="{C}" width="1" height="1" fill="#000" fill-opacity="0"/>'
                     f'<rect x="{bx+C}" y="{C}" width="1" height="1" fill="currentColor" class="ColorScheme-Background"/>')
    out['right'] = edge('right', bx + C + 1, C, C, 1)
    out['bottom'] = edge('bottom', bx + C, C + 1, 1, C)
    return out


def mask(R, my):
    """Blur-mask tiles: quarter discs of radius R in the corners, solid elsewhere. Sheet origin (0, my)."""
    out = {}
    cx = {'left': 0, 'center': R, 'right': R + 1}
    cy = {'top': my, 'center': my + R, 'bottom': my + R + 1}
    w = {'left': R, 'center': 1, 'right': R}
    h = {'top': R, 'center': 1, 'bottom': R}
    for vy in ('top', 'center', 'bottom'):
        for hx in ('left', 'center', 'right'):
            name = 'center' if (vy, hx) == ('center', 'center') else ('' if vy == 'center' else vy) + ('' if hx == 'center' else hx)
            x, y, ww, hh = cx[hx], cy[vy], w[hx], h[vy]
            g = f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" fill="#000" fill-opacity="0"/>'
            if vy != 'center' and hx != 'center':
                d = {'topleft':     f'M{x+R} {y} L{x+R} {y} A{R} {R} 0 0 0 {x} {y+R} L{x} {y+R} L{x+R} {y+R} Z',
                     'topright':    f'M{x} {y} L{x} {y} A{R} {R} 0 0 1 {x+R} {y+R} L{x+R} {y+R} L{x} {y+R} Z',
                     'bottomleft':  f'M{x+R} {y+R} L{x+R} {y+R} A{R} {R} 0 0 1 {x} {y} L{x} {y} L{x+R} {y} Z',
                     'bottomright': f'M{x} {y+R} L{x} {y+R} A{R} {R} 0 0 0 {x+R} {y} L{x+R} {y} L{x} {y} Z'}[name]
                g += f'<path d="{d}" fill="#000000"/>'
            else:
                g += f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" fill="#000000"/>'
            out['mask-' + name] = g
    return out


def generate(svg, R):
    """Return svg with its body tiles, mask tiles and hints rebuilt for corner radius R."""
    head = HEADER.match(svg)
    assert head, 'unexpected svg header'
    ring = 'hl-top' in svg
    my = int(re.search(r'<g id="mask-topleft"><rect x="0" y="(\d+)"', svg).group(1))
    # the shadow sheet is not ours: find how far right and down it reaches, and put the body beside it
    right = bottom = 0.0
    for m in re.finditer(r'<g id="shadow-[a-z]+"><rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', svg):
        x, y, w, h = (float(v) for v in m.groups()); right = max(right, x + w); bottom = max(bottom, y + h)
    for m in re.finditer(r'<rect id="shadow-hint-[a-z]+-margin" x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', svg):
        x, y, w, h = (float(v) for v in m.groups()); right = max(right, x + w); bottom = max(bottom, y + h)
    C = R + 2
    bx = math.ceil(right) + 2
    hint_x = bx + 2 * C + 3                 # body content-margin hints, right of the body
    mask_hint_x = 2 * R + 3                 # mask hints, right of the mask
    W = hint_x + 6
    H = max(math.ceil(bottom), my + 2 * R + 1) + 6

    nb, nm = body(R, ring, bx), mask(R, my)
    for name, g in {**{n: nb[n] for n in ORDER}, **nm}.items():
        svg, k = re.subn(rf'<g id="{name}">.*?</g>', lambda _m, name=name, g=g: f'<g id="{name}">{g}</g>', svg, count=1, flags=re.S)
        assert k == 1, name
    for prefix, x in (('hint', hint_x), ('mask-hint', mask_hint_x)):
        for side in ('left', 'top', 'right', 'bottom'):
            svg, k = re.subn(rf'(<rect id="{prefix}-{side}-margin" x=")[\d.]+(")', lambda _m, x=x: f'{_m.group(1)}{x}{_m.group(2)}', svg)
            assert k == 1, f'{prefix}-{side}'
    return svg.replace(head.group(0), f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default=str(DEFAULT_ROOT), help='plasma/desktoptheme directory (default %(default)s)')
    ap.add_argument('--check', action='store_true', help='write nothing; exit 1 if a file differs from what the radii would give')
    args = ap.parse_args()
    stale = False
    for theme in THEMES:
        for rel, R in OWNED:
            p = pathlib.Path(args.root) / theme / rel
            old = p.read_text(); new = generate(old, R)
            if new != old:
                stale = True
                if not args.check:
                    p.write_text(new)
            print(('would change ' if args.check and new != old else 'wrote ' if new != old else 'unchanged ') + f'{theme}/{rel} (radius {R})')
    sys.exit(1 if args.check and stale else 0)


if __name__ == '__main__':
    main()
