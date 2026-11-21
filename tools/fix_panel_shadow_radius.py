#!/usr/bin/env python3
"""Grow the corner radius baked into the dock shadow art (plasma widgets/panel-background.svg) by DELTA px.

    python3 tools/fix_panel_shadow_radius.py [--delta 4]      run from the repo root, then run tools/gen_panel_variants.py

Why: tools/gen_panel_frame.py rebuilds the body tiles for radii.DOCK but leaves the shadow tiles alone. Those were drawn for a 6px
window, so the near-black contact layer (6.5px corner) stays sharper than a 10px body and shows as black wedges in the corners.
Every shadow layer is a rounded rectangle whose outer edges stay put; only its corner arc gets rounder (r -> r + delta).
NOT idempotent: it adds delta every time it runs. Only run it once per radius change (6 -> 10 is delta 4).
"""
import argparse, pathlib, re

ap = argparse.ArgumentParser()
ap.add_argument('--delta', type=float, default=4.0)
ap.add_argument('--root', default='plasma/desktoptheme')
args = ap.parse_args()
d = args.delta

PATH = re.compile(r'M([\d.]+) ([\d.]+) L([\d.]+) ([\d.]+) A([\d.]+) ([\d.]+) 0 0 ([01]) ([\d.]+) ([\d.]+) L([\d.]+) ([\d.]+) L([\d.]+) ([\d.]+) Z')
f = lambda v: ('%.3f' % v).rstrip('0').rstrip('.')

def grow(m):
    ax, ay, cx, cy, r, _, sw, ex, ey, fx, fy, gx, gy = m.groups()
    ax, ay, cx, cy, r, ex, ey, fx, fy, gx, gy = map(float, (ax, ay, cx, cy, r, ex, ey, fx, fy, gx, gy))
    r2 = r + d
    sgn = lambda v: 1 if v >= 0 else -1
    cx2 = ex + sgn(cx - ex) * r2        # arc starts r2 away from the vertical edge
    ey2 = cy + sgn(ey - cy) * r2        # and ends r2 away from the horizontal edge
    return (f'M{f(ax)} {f(ay)} L{f(cx2)} {f(cy)} A{f(r2)} {f(r2)} 0 0 {sw} {f(ex)} {f(ey2)} L{f(fx)} {f(fy)} L{f(gx)} {f(gy)} Z')

for theme in ('halcyon-glass-dark', 'halcyon-glass-light'):
    p = pathlib.Path(args.root) / theme / 'widgets/panel-background.svg'
    s = p.read_text(); n = 0
    def tile(m):
        global n
        body, k = PATH.subn(grow, m.group(2)); n += k
        return m.group(1) + body + m.group(3)
    s = re.sub(r'(<g id="shadow-(?:topleft|topright|bottomleft|bottomright)">)(.*?)(</g>)', tile, s, flags=re.S)
    p.write_text(s)
    print(f'{theme}: grew {n} shadow arcs by {d}px')
