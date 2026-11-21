#!/usr/bin/env python3
"""Regenerate the frame pieces of the Plasma dialog background (macOS alert) from the Tokens::Alert tokens.
Usage: gen_alert.py <halcyon-global dir>

Light: 70% window colour + 10% #BFBFBF fill, 0.5px #DBDBDB hairline, inner top/bottom light band.
Dark:  flat fill, 1px black 20% outline, 1px inner highlight, light band; all rebuilt from the radius.
Corner radius 10 (cell 12, piece 25), the same as the Aurorae window decoration. The drop shadow is NOT drawn here: tools/gen_popup_shadow.py owns the shadow-* pieces.

Why every piece is built from real geometry (no clip-path): Plasma's FrameSvg sizes each element (topleft, top, ...) with
QSvgRenderer::boundsOnElement, and Qt SVG ignores clip-path when it measures. The old light pieces were a full 17x17 rounded
rect clipped to the 8x8 cell, so each cell measured as 17x17 and the dialog drew as a scalloped border of tiled corners with a
huge inner radius. Each piece below only contains shapes that lie inside its own cell.
"""
import re, sys, math
import radii                # tools/radii.py: the corner radius lives there
root = sys.argv[1] if len(sys.argv) > 1 else '.'
R = radii.DIALOG            # corner radius (same surface radius as the Aurorae window frame)
C = R + 2                   # cell size
W = 2 * C + 1               # piece size: 8 + 1 + 8
HAIR = 0.5                  # hairline width

def cdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))

# Inner light band (#282828, plus-lighter, inner shadow offset +-40, blur sigma 5). Only the top and bottom edges get it.
# Strength at depth d from the edge = peak * (1 - cdf(d / sigma)): peak 15.7% (light) / 10.2% (dark) at the edge, gone by ~6px at sigma 2.5.
# Qt SVG has no plus-lighter, so it is white at that opacity; the light variant gets a gain because white-at-alpha adds less than
# a true additive blend on a bright backdrop.
# The notification variant tightens it: sigma 2.5, and its dark material uses #1A1A1A instead of #282828. Plasma notification popups, the
# calendar and the OSD all share dialogs/background, so the one SVG takes the notification values.
BAND_SIG = 2.5
BAND_PEAK = dict(light=0x28 / 255, dark=0x1A / 255)
BAND_GAIN = dict(light=3.0, dark=1.0)

def band_defs(variant, with_shape):
    g = BAND_GAIN[variant]
    stops = ''.join(f'<stop offset="{d/10:.2f}" stop-color="#fff" stop-opacity="{min(1.0, g*BAND_PEAK[variant]*(1-cdf(d/BAND_SIG))):.4f}"/>'
                    for d in range(0, 11))
    out = ('<linearGradient id="band-top" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="10">' + stops + '</linearGradient>'
           f'<linearGradient id="band-bot" gradientUnits="userSpaceOnUse" x1="0" y1="{W}" x2="0" y2="{W-10}">' + stops + '</linearGradient>')
    if with_shape:
        out += f'<clipPath id="band-shape"><rect x="0" y="0" width="{W}" height="{W}" rx="{R}"/></clipPath>'
    return out

# piece -> (x, y, w, h) in the file
FRAME = {
 'topleft': (0, 0, C, C), 'top': (C, 0, 1, C), 'topright': (C+1, 0, C, C),
 'left': (0, C, C, 1), 'center': (C, C, 1, 1), 'right': (C+1, C, C, 1),
 'bottomleft': (0, C+1, C, C), 'bottom': (C, C+1, 1, C), 'bottomright': (C+1, C+1, C, C)}
BAND_PIECES = ('topleft', 'top', 'topright', 'bottomleft', 'bottom', 'bottomright')
CORNERS = ('topleft', 'topright', 'bottomleft', 'bottomright')

def n(v): return f'{v:.4g}'

def corner_path(k, inset=0.0):
    """Quarter of the rounded rect that falls inside cell k, shrunk by `inset` on the outer edges. Only the outer edges are inset."""
    x, y, w, h = FRAME[k]
    r = R - inset
    t, l, b, rt = (inset, inset, W - inset, W - inset)    # outer edges of the whole 17x17 shape, inset
    if k == 'topleft':
        return f'M{x+w} {t} L{l+r} {t} A{r} {r} 0 0 0 {l} {t+r} L{l} {y+h} L{x+w} {y+h} Z'
    if k == 'topright':
        return f'M{x} {t} L{rt-r} {t} A{r} {r} 0 0 1 {rt} {t+r} L{rt} {y+h} L{x} {y+h} Z'
    if k == 'bottomleft':
        return f'M{l} {y} L{l} {b-r} A{r} {r} 0 0 0 {l+r} {b} L{x+w} {b} L{x+w} {y} Z'
    return f'M{x} {b} L{rt-r} {b} A{r} {r} 0 0 0 {rt} {b-r} L{rt} {y} L{x} {y} Z'

def hair_rect(k):
    x, y, w, h = FRAME[k]
    if k == 'top':    return (x, y, w, HAIR)
    if k == 'bottom': return (x, y + h - HAIR, w, HAIR)
    if k == 'left':   return (x, y, HAIR, h)
    if k == 'right':  return (x + w - HAIR, y, HAIR, h)
    return None

def band_grad(k): return 'band-top' if FRAME[k][1] == 0 else 'band-bot'

def piece_light(k):
    x, y, w, h = FRAME[k]
    o = [f'<g id="{k}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>']
    if k in CORNERS:
        d = corner_path(k)
        o.append(f'<path d="{d}" fill="currentColor" class="ColorScheme-Background" fill-opacity="0.7"/>')
        o.append(f'<path d="{d}" fill="#BFBFBF" fill-opacity="0.1"/>')
        if k in BAND_PIECES: o.append(f'<path class="lightband" d="{d}" fill="url(#{band_grad(k)})"/>')
        o.append(f'<path d="{d} {corner_path(k, HAIR)}" fill="#DBDBDB" fill-rule="evenodd"/>')
    else:
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="currentColor" class="ColorScheme-Background" fill-opacity="0.7"/>')
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#BFBFBF" fill-opacity="0.1"/>')
        if k in BAND_PIECES: o.append(f'<rect class="lightband" x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{band_grad(k)})"/>')
        hr = hair_rect(k)
        if hr: o.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#DBDBDB"/>' % tuple(n(v) for v in hr))
    o.append('</g>\n')
    return ''.join(o)

def replace_group(s, gid, new):
    # a frame piece is one <g id="gid"> ... </g>; its children may contain one nested <g> (older versions), so match up to the next piece
    pat = r'<g id="%s">(?:(?!<g id=).)*?</g>(?:\s*</g>)?\n' % re.escape(gid)
    out, cnt = re.subn(pat, lambda m: new, s, count=1, flags=re.S)
    if cnt != 1: raise SystemExit(f'piece {gid} not found')
    return out


def piece_dark(k):
    x, y, w, h = FRAME[k]
    o = [f'<g id="{k}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>']
    top = FRAME[k][1] == 0
    if k in CORNERS:
        d = corner_path(k)
        o.append(f'<path d="{d}" fill="currentColor" class="ColorScheme-Background"/>')
        o.append(f'<path fill="#000000" fill-opacity="0.2" fill-rule="evenodd" d="{d} {corner_path(k, 1)}"/>')
        o.append(f'<path fill="url(#hl-{"top" if top else "bottom"})" fill-rule="evenodd" d="{corner_path(k, 1)} {corner_path(k, 2)}"/>')
    else:
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="currentColor" class="ColorScheme-Background"/>')
        if k == 'top':
            o.append(f'<rect x="{x}" y="{y}" width="{w}" height="1" fill="#000000" fill-opacity="0.2"/><rect x="{x}" y="{y+1}" width="{w}" height="1" fill="#ffffff" fill-opacity="0.12"/>')
        elif k == 'bottom':
            o.append(f'<rect x="{x}" y="{y+h-1}" width="{w}" height="1" fill="#000000" fill-opacity="0.2"/><rect x="{x}" y="{y+h-2}" width="{w}" height="1" fill="#ffffff" fill-opacity="0.12"/>')
        elif k == 'left':
            o.append(f'<rect x="{x}" y="{y}" width="1" height="{h}" fill="#000000" fill-opacity="0.2"/><rect x="{x+1}" y="{y}" width="1" height="{h}" fill="#ffffff" fill-opacity="0.05"/>')
        elif k == 'right':
            o.append(f'<rect x="{x+w-1}" y="{y}" width="1" height="{h}" fill="#000000" fill-opacity="0.2"/><rect x="{x+w-2}" y="{y}" width="1" height="{h}" fill="#ffffff" fill-opacity="0.05"/>')
    if k in BAND_PIECES:
        o.append(f'<rect class="lightband" x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{band_grad(k)})" clip-path="url(#band-shape)"/>')
    o.append('</g>\n')
    return ''.join(o)

def mask_piece(k):
    """Blur mask: black quarter discs of radius R in the corners, black 1px strips between. Rows start at MY."""
    MY = 114
    cols = {'left': 0, 'center': R, 'right': R + 1}; rows = {'top': MY, 'mid': MY + R, 'bottom': MY + R + 1}
    name = k.replace('mask-', '')
    v = 'top' if name.startswith('top') else 'bottom' if name.startswith('bottom') else 'mid'
    hh = 'left' if name.endswith('left') else 'right' if name.endswith('right') else 'center'
    if name in ('top', 'bottom'): hh = 'center'
    if name in ('left', 'right'): v = 'mid'
    if name == 'center': v, hh = 'mid', 'center'
    x, y = cols[hh], rows[v]
    w = 1 if hh == 'center' else R; h = 1 if v == 'mid' else R
    if name in CORNERS_NAMES:
        if name == 'topleft':      d = f'M{x+R} {y} A{R} {R} 0 0 0 {x} {y+R} L{x+R} {y+R} Z'
        elif name == 'topright':   d = f'M{x} {y} A{R} {R} 0 0 1 {x+R} {y+R} L{x} {y+R} Z'
        elif name == 'bottomleft': d = f'M{x+R} {y+R} A{R} {R} 0 0 1 {x} {y} L{x+R} {y} Z'
        else:                      d = f'M{x} {y+R} A{R} {R} 0 0 0 {x+R} {y} L{x} {y} Z'
        shape = f'<path d="{d}" fill="#000000"/>'
    else:
        shape = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000000"/>'
    return f'<g id="mask-{name}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>{shape}</g>\n'

CORNERS_NAMES = ('topleft', 'topright', 'bottomleft', 'bottomright')

def relayout(s):
    """Frame cells grew with the radius, so move the content-margin hints out of the way and rebuild the blur mask."""
    s = re.sub(r'<rect id="(?:mask-)?hint-(?:left|top|right|bottom)-margin"[^>]*/>\n?', '', s)
    s = re.sub(r'<g id="mask-\w+">.*?</g>\n?', '', s, flags=re.S)
    hints = ''.join(f'<rect id="hint-{n}-margin" x="40" y="0" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>\n'
                    for n, w, h in (('left', 8, 1), ('top', 1, 8), ('right', 8, 1), ('bottom', 1, 8)))
    masks = ''.join(mask_piece(k) for k in ('topleft', 'top', 'topright', 'left', 'center', 'right', 'bottomleft', 'bottom', 'bottomright'))
    mh = ''.join(f'<rect id="mask-hint-{n}-margin" x="30" y="114" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>\n'
                 for n, w, h in (('left', 0.01, 1), ('top', 1, 0.01), ('right', 0.01, 1), ('bottom', 1, 0.01)))
    i = s.index('<rect id="shadow-hint-left-margin"')
    return s[:i] + hints + s[i:].replace('</svg>', masks + mh + '</svg>')

def build(variant):
    p = f'{root}/plasma/desktoptheme/halcyon-glass-{variant}/dialogs/background.svg'
    s = open(p).read()
    s = re.sub(r'<clipPath id="fr-[a-z]+">.*?</clipPath>', '', s, flags=re.S)
    s = re.sub(r'<linearGradient id="band-(?:top|bot)".*?</linearGradient>|<clipPath id="band-shape">.*?</clipPath>', '', s, flags=re.S)
    s = s.replace('</defs>', band_defs(variant, variant == 'dark') + '</defs>', 1)
    for k in FRAME: s = replace_group(s, k, piece_light(k) if variant == 'light' else piece_dark(k))
    s = relayout(s)
    open(p, 'w').write(s)
    print('wrote', p, len(s))

if __name__ == '__main__':
    for v in ('light', 'dark'): build(v)
