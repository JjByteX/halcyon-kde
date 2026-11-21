#!/usr/bin/env python3
"""Writes close/minimize/maximize/restore.svg for the four Halcyon Aurorae themes.

Run from the halcyon folder:  python3 tools/gen_buttons.py     (needs numpy, scipy, pillow)

The coloured discs are modelled on the macOS traffic lights, fitted by button_render.py into plain SVG gradients (vector, sharp at any scale).
Every state is an 18x20 cell (14px disc at x=2,y=0.5, shadow room below), drawn 1:1 so the disc is exactly 14px.
Matching theme settings: ButtonWidth=18, ButtonHeight=20, ButtonSpacing=5 (23px pitch), TitleEdgeLeft=6, ButtonMarginTop=0.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import button_render as fb

W, H = fb.W, fb.H
CXL, CYL = fb.CX, fb.CY            # disc centre inside a cell (9, 7.5)
ROOT = os.path.join(os.path.dirname(__file__), '..', 'aurorae', 'themes')

def disc_defs(name):
    """Resolution-independent version of the disc: vertical gradient sampled from the full render (core look),
    a soft rim, the two side slivers and the drop shadow. Everything is plain gradients/paths, which Qt SVG draws sharply at any scale."""
    import numpy as np
    S = fb.S
    p = fb.BTN[name]
    core = fb.render(name, rims=False)
    a = core[..., 3:]; rgb = np.where(a > 1e-6, core[..., :3] / np.maximum(a, 1e-6), 0)
    cx = int(fb.CX * S)
    stops = []
    N = 28
    for i in range(N + 1):
        t = i / N
        y = int((fb.CY - 6.95 + t * 13.9) * S)
        c = rgb[y, cx - S:cx + S].mean(axis=0)
        stops.append(f'<stop offset="{t:.4f}" stop-color="#{int(c[0]*255+.5):02x}{int(c[1]*255+.5):02x}{int(c[2]*255+.5):02x}"/>')
    rim = '#%02x%02x%02x' % tuple(int(v * 255 + .5) for v in p['rim'])
    drop = '#%02x%02x%02x' % tuple(int(v * 255 + .5) for v in p['drop'])
    R = fb.R
    # side slivers: part of the disc outside a circle of r R+1.5 shifted by +-2 (spread 1.5, dx +-2)
    xi = (R * R - (R + 1.4) ** 2 + 4) / 4.0            # x of the circle intersections (relative, shifted circle at +2)
    yi = (R * R - xi * xi) ** 0.5
    left  = f'M{xi:.4f},{-yi:.4f}A{R},{R} 0 0 0 {xi:.4f},{yi:.4f}A{R+1.4},{R+1.4} 0 0 1 {xi:.4f},{-yi:.4f}Z'
    right = f'M{-xi:.4f},{-yi:.4f}A{R},{R} 0 0 1 {-xi:.4f},{yi:.4f}A{R+1.4},{R+1.4} 0 0 0 {-xi:.4f},{-yi:.4f}Z'
    return (f'<linearGradient id="fill" gradientUnits="userSpaceOnUse" x1="0" y1="{-R+0.05}" x2="0" y2="{R-0.05}">{"".join(stops)}</linearGradient>'
            f'<radialGradient id="rim" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="{R}"><stop offset="0.78" stop-color="{rim}" stop-opacity="0"/>'
            f'<stop offset="0.88" stop-color="{rim}" stop-opacity="0.10"/><stop offset="0.95" stop-color="{rim}" stop-opacity="0.26"/>'
            f'<stop offset="0.985" stop-color="{rim}" stop-opacity="0.42"/><stop offset="1" stop-color="{rim}" stop-opacity="0.50"/></radialGradient>'
            f'<radialGradient id="shadow" gradientUnits="userSpaceOnUse" cx="0" cy="1.5" r="8.2"><stop offset="0.78" stop-color="{drop}" stop-opacity="0.15"/>'
            f'<stop offset="0.86" stop-color="{drop}" stop-opacity="0.09"/><stop offset="0.93" stop-color="{drop}" stop-opacity="0.03"/>'
            f'<stop offset="1" stop-color="{drop}" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="sl" gradientUnits="userSpaceOnUse" x1="-7" y1="0" x2="-6.4" y2="0"><stop offset="0" stop-color="{rim}"/><stop offset="0.33" stop-color="{rim}"/>'
            f'<stop offset="0.75" stop-color="{rim}" stop-opacity="0.5"/><stop offset="1" stop-color="{rim}" stop-opacity="0.1"/></linearGradient>'
            f'<linearGradient id="sr" gradientUnits="userSpaceOnUse" x1="7" y1="0" x2="6.4" y2="0"><stop offset="0" stop-color="{rim}"/><stop offset="0.33" stop-color="{rim}"/>'
            f'<stop offset="0.75" stop-color="{rim}" stop-opacity="0.5"/><stop offset="1" stop-color="{rim}" stop-opacity="0.1"/></linearGradient>'
            f'<g id="disc"><circle cx="0" cy="1.5" r="8.2" fill="url(#shadow)"/><circle r="{R}" fill="url(#fill)"/><circle r="{R}" fill="url(#rim)"/>'
            f'<path d="{left}" fill="url(#sl)"/><path d="{right}" fill="url(#sr)"/></g>')


# Apple's dark-mode traffic lights, fitted to a 2x screenshot of the real thing (macOS dark mode):
# saturated top, a soft lighter glow in the lower centre, and a LIGHT tinted rim that is brightest at the top and bottom edges
# (light mode has a dark rim instead). No drop shadow on dark titlebars.
# The glow is a disc-sized circle filled with the radial gradient (transparent past its radius), NOT a circle clipped with clip-path:
# Qt SVG does not honour that clip inside a <use>d group, so the glow used to spill below the button.
DARK = {
    'close': dict(v=[(0, (231,111,98)), (.143, (229,105,92)), (.214, (228,99,85)), (.286, (227,93,78)), (.357, (226,93,78)), (1, (225,94,79))],
                  glow=(222,112,101), rim=(254,162,152)),
    'min':   dict(v=[(0, (239,184,54)), (.143, (240,183,34)), (.214, (240,181,0)), (.357, (240,183,0)), (1, (241,185,0))],
                  glow=(246,207,82), rim=(254,238,110)),
    'max':   dict(v=[(0, (110,194,67)), (.143, (100,191,49)), (.214, (89,188,5)), (.286, (78,186,0)), (.357, (77,185,0)), (1, (80,186,0))],
                  glow=(111,192,78), rim=(155,236,119)),
}
hexc = lambda c: '#%02x%02x%02x' % tuple(c)

def disc_defs_dark(name):
    d = DARK[name]; R = fb.R
    st = ''.join(f'<stop offset="{t}" stop-color="{hexc(c)}"/>' for t, c in d['v'])
    gl, rm = hexc(d['glow']), hexc(d['rim'])
    ring = [(0, 1), (.14, .7), (.3, .32), (.5, .24), (.7, .32), (.86, .7), (1, 1)]
    return (f'<linearGradient id="fill" gradientUnits="userSpaceOnUse" x1="0" y1="{-R}" x2="0" y2="{R}">{st}</linearGradient>'
            f'<radialGradient id="glow" gradientUnits="userSpaceOnUse" cx="0" cy="4.2" r="5.6"><stop offset="0" stop-color="{gl}"/>'
            f'<stop offset="0.45" stop-color="{gl}" stop-opacity="0.9"/><stop offset="0.7" stop-color="{gl}" stop-opacity="0.5"/>'
            f'<stop offset="1" stop-color="{gl}" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="ring" gradientUnits="userSpaceOnUse" x1="0" y1="{-R}" x2="0" y2="{R}">'
            + ''.join(f'<stop offset="{t}" stop-color="{rm}" stop-opacity="{a}"/>' for t, a in ring) + '</linearGradient>'
            f'<g id="disc"><circle r="{R}" fill="url(#fill)"/><circle r="{R}" fill="url(#glow)"/>'
            f'<circle r="{R - 0.36}" fill="none" stroke="url(#ring)" stroke-width="0.72"/></g>')

# glyphs, centred on (0,0), drawn on hover/press
def sym_close():
    st = 'fill="none" stroke="#7d0008" stroke-width="1.64" stroke-linecap="round"'
    return f'<path {st} d="M-2.18,-2.18L2.18,2.18"/><path {st} d="M2.18,-2.18L-2.18,2.18"/>'
def sym_min():
    return '<path fill="none" stroke="#a76900" stroke-width="2" stroke-linecap="round" d="M-3,0H3"/>'
# maximize: two triangles pointing outwards (coordinates are the originals, centre (24,8)) ; restore: the originals rotated
_TRI_A = 'm 21.505799,5.0003871 c -0.30878,-0.01294 -0.548384,0.306848 -0.499426,0.601487 v 2.900024 c -0.01384,0.348024 0.396104,0.611511 0.706219,0.451115 0.176482,-0.09375 0.296306,-0.263657 0.442851,-0.396434 l 2.700021,-2.702784 c 0.257383,-0.234914 0.153718,-0.703938 -0.169727,-0.818256 -0.149723,-0.05391 -0.310149,-0.02642 -0.466261,-0.03516 z'
_TRI_B = 'm 26.529321,7.0001351 c -0.08182,-0.0076 -0.164381,0.0068 -0.24191,0.04686 -0.176482,0.09375 -0.296305,0.261706 -0.44285,0.394481 L 23.14454,10.146213 c -0.257383,0.234914 -0.153717,0.703938 0.169727,0.818257 0.149724,0.05391 0.308199,0.02642 0.46431,0.03515 h 2.715629 c 0.30878,0.01294 0.548383,-0.308802 0.499426,-0.60344 V 7.4981051 c 0.01038,-0.261013 -0.218856,-0.475081 -0.464311,-0.497979 z'
def sym_max():
    return f'<g transform="translate(-24,-8)" fill="#0f7901"><path d="{_TRI_A}"/><path d="{_TRI_B}"/></g>'
_RES_A = 'm 23.529321,3.5001392 c -0.08182,-0.0076 -0.164381,0.0068 -0.24191,0.04686 -0.176482,0.09375 -0.296305,0.261706 -0.44285,0.394481 L 20.14454,6.6462171 c -0.257383,0.234914 -0.153717,0.703938 0.169727,0.818257 0.149724,0.05391 0.308199,0.02642 0.46431,0.03515 h 2.715629 c 0.30878,0.01294 0.548383,-0.308802 0.499426,-0.60344 V 3.9981092 c 0.01038,-0.261013 -0.218856,-0.475081 -0.464311,-0.497979 z'
_RES_B = 'm 24.505459,7.5000422 c -0.30878,-0.01294 -0.548384,0.306848 -0.499426,0.601487 v 2.9000238 c -0.01384,0.348024 0.396104,0.611511 0.706219,0.451115 0.176482,-0.09375 0.296306,-0.263657 0.442851,-0.396434 l 2.700021,-2.7027838 c 0.257383,-0.234914 0.153718,-0.703938 -0.169727,-0.818256 -0.149723,-0.05391 -0.310149,-0.02642 -0.466261,-0.03516 z'
def sym_restore():
    # original net transform translate(-11,16) . rotate(-90, 21.75,-5.75) puts the glyph centre at (24,7.5); recentre on 0,0
    return (f'<g transform="translate(-24,-7.5) translate(-11,16) rotate(-90,21.75,-5.7503379)" fill="#0f7901">'
            f'<path d="{_RES_A}"/><path d="{_RES_B}"/></g>')
SYMS = {'close': ('close', sym_close), 'minimize': ('min', sym_min), 'maximize': ('max', sym_max), 'restore': ('max', sym_restore)}

# inactive discs / pressed tint, per theme (same values as the previous theme files)
def inactive(day):
    if day:
        return ('<circle cx="0" cy="0" r="6.85" fill="#000" opacity="0.1"/>'
                '<circle cx="0" cy="0" r="6.85" fill="none" stroke="#000" stroke-opacity="0.1" stroke-width="0.85"/>'
                '<circle cx="0" cy="0" r="5.75" fill="none" stroke="#fff" stroke-opacity="0.1" stroke-width="0.5"/>')
    return '<circle cx="0" cy="0" r="6.85" fill="#fff" opacity="0.25"/>'
def tint(day): return f'<circle cx="0" cy="0" r="7" fill="#000" opacity="{0.25 if day else 0.5}"/>'

def sheet(kind, day):
    img_key, sym = SYMS[kind]
    defs = disc_defs(img_key) if day else disc_defs_dark(img_key)
    base = '<use xlink:href="#disc"/>'
    hover = base + sym()
    pressed = hover + tint(day)
    ina = inactive(day)
    els = [('active-center', 0, 0, base), ('hover-center', 1, 0, hover), ('pressed-center', 2, 0, pressed),
           ('deactivated-center', 3, 0, ina),
           ('inactive-center', 0, 1, ina), ('hover-inactive-center', 1, 1, hover), ('pressed-inactive-center', 2, 1, pressed),
           ('deactivated-inactive-center', 3, 1, ina + tint(day))]
    out = [f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'width="{4 * W}" height="{2 * H}" viewBox="0 0 {4 * W} {2 * H}">',
           f'<defs>{defs}</defs>']
    for name, i, j, body in els:
        x, y = i * W, j * H
        out.append(f'<g id="{name}"><rect x="{x}" y="{y}" width="{W}" height="{H}" fill="#000" fill-opacity="0.003"/>'
                   f'<g transform="translate({x + CXL},{y + CYL})">{body}</g></g>')
    out.append('</svg>\n')
    return '\n'.join(out)

if __name__ == '__main__':
    for theme in sorted(os.listdir(ROOT)):
        day = 'day' in theme
        for kind in SYMS:
            path = os.path.join(ROOT, theme, f'{kind}.svg')
            if not os.path.isdir(os.path.dirname(path)): continue
            open(path, 'w').write(sheet(kind, day))
        # layout keys that go with the 18x20 cells
        rc = [f for f in os.listdir(os.path.join(ROOT, theme)) if f.endswith('rc')][0]
        rp = os.path.join(ROOT, theme, rc); lines = open(rp).read().splitlines()
        want = {'ButtonWidth': str(W), 'ButtonHeight': str(H), 'ButtonSpacing': '5', 'ButtonMarginTop': '0', 'TitleEdgeLeft': '6', 'TitleEdgeLeftMaximized': '6'}
        lines = [f'{l.split("=")[0]}={want[l.split("=")[0]]}' if '=' in l and l.split('=')[0] in want else l for l in lines]
        open(rp, 'w').write('\n'.join(lines) + '\n')
        print('wrote', theme)
