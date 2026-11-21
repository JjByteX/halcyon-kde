#!/usr/bin/env python3
"""Generates the four Halcyon Aurorae decoration.svg files from measured macOS 27 values.

Run from the halcyon folder:  python3 tools/gen_decoration_macos.py

Values (large window):
  corner radius 10 (radii.WINDOW; Halcyon does not follow macOS's 26. Top corners only: the bottom edge is square because KWin cannot round a client's bottom corners), titlebar 32px (day #F6F6F6 / night #2A2A2A, same as the Header colour so titlebar and menubar match; blur variants 85%, 0.67px divider black 5%), window shadow dy 18 / sigma 27 / 30% black,
  plus a ~1px outline (black 80% blurred 0.5, i.e. about 40% at the edge).
Qt SVG has no blur filter, so the shadow is built from erf gradients (exact for a straight edge, radial for corners).
"""
import math
import radii   # tools/radii.py
phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))

# ---- geometry (all in px) ----
R   = radii.WINDOW   # corner radius (tools/radii.py)
TB  = 32      # titlebar height                     
DY  = 18      # shadow offset
SIG = 27      # shadow sigma                        
A   = 0.30    # shadow alpha
PL  = 54      # shadow room left/right (2 sigma)
PT  = 36      # shadow room above  (2 sigma - dy)
PB  = 72      # shadow room below  (2 sigma + dy)
BB  = 0       # bottom border (rc BorderBottom): none, like Breeze and macOS (was 4)
BL  = 1       # side border   (rc BorderLeft/Right)

W0   = 120                 # corner/left column width (wide enough that the side shadow has fully faded in)
CTOP = max(PT + R + DY, PT + TB)   # top corner cell height: reaches the shadow circle centre and the whole titlebar (incl. divider)
MID  = 45                  # middle row height (stretches)
FB   = 40                  # bottom cell: frame bottom edge at this local y (room above so the shadow's y-fade is ~1 at the top)
CBOT = FB + PB             # 112 bottom cell height
STRIP = 3                  # bottom corner shadow is built from vertical strips of this width
SETW = 3 * W0              # width of one set of 9 cells
Y_MID, Y_BOT = CTOP, CTOP + MID

def stops(f, n=32):
    return ''.join(f'<stop offset="{i/n:.4f}" stop-color="#000" stop-opacity="{f(i/n):.4f}"/>' for i in range(n + 1))

def build(fill_a, inactive_scale=0.55, color='#fff', div_a=0.05, outline_a=0.30, hi_a=0.0):
    out = [f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{2*SETW+160}" height="{CTOP+MID+CBOT+20}" viewBox="0 0 {2*SETW+160} {CTOP+MID+CBOT+20}">\n<defs>']
    RR = R + 3 * SIG
    for p, sc in (('a', 1.0), ('i', inactive_scale)):
        a = A * sc
        # left/right edge: shadow shape's straight edge sits at x = PL
        out.append(f'<linearGradient id="{p}L" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W0}" y2="0">{stops(lambda t: a*phi((t*W0-PL)/SIG))}</linearGradient>')
        # top edge: shadow shape starts DY lower than the window
        out.append(f'<linearGradient id="{p}T" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{PT}">{stops(lambda t: a*phi((t*PT-(PT+DY))/SIG))}</linearGradient>')
        # bottom edge: frame bottom is at local y=FB, shadow shape ends DY below it
        out.append(f'<linearGradient id="{p}B" gradientUnits="userSpaceOnUse" x1="0" y1="{Y_BOT+FB}" x2="0" y2="{Y_BOT+CBOT}">{stops(lambda t: a*phi((FB+DY-(FB+t*PB))/SIG)*phi((W0-PL)/SIG))}</linearGradient>')
        # square bottom corners: shadow of a sharp rectangle is separable, shade(x)*shade(y), so one vertical-strip gradient per column
        for xi in range(0, W0, STRIP):
            lx = phi((xi + STRIP / 2 - PL) / SIG)
            fy = lambda y: phi((FB + DY - y) / SIG)
            ys = [0, FB * 0.5, FB] + [FB + PB * k / 12 for k in range(1, 13)]
            st = ''.join(f'<stop offset="{y/CBOT:.4f}" stop-color="#000" stop-opacity="{a*lx*fy(y):.4f}"/>' for y in ys)
            out.append(f'<linearGradient id="{p}S{xi}" gradientUnits="userSpaceOnUse" x1="0" y1="{Y_BOT}" x2="0" y2="{Y_BOT+CBOT}">{st}</linearGradient>')
        for nm, cx, cy in (('RT', PL + R, PT + R + DY),):
            out.append(f'<radialGradient id="{p}{nm}" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" fx="{cx}" fy="{cy}" r="{RR}">{stops(lambda t: a*phi((R-t*RR)/SIG), 40)}</radialGradient>')
    out.append('</defs>')
    F = f'fill="{color}" fill-opacity="{fill_a}"'
    O = f'fill="#000" fill-opacity="{outline_a}"'
    D = f'fill="#000" fill-opacity="{div_a}"'
    H = f'fill="#fff" fill-opacity="{hi_a}"'
    bound = lambda x, y, w, h: f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0.003"/>'

    def cell(name, x, y, w, h, body, off, mirror=False):
        tf = f'matrix(-1,0,0,1,{SETW+off},0)' if mirror else (f'translate({off},0)' if off else '')
        t = f' transform="{tf}"' if tf else ''
        return f'<g id="{name}"{t}>{bound(x,y,w,h)}{body}</g>'

    for p, pre, off in (('a', 'decoration', 0), ('i', 'decoration-inactive', SETW + 20)):
        cy2 = PT + R   # frame corner centre y
        # --- top-left corner: shadow (outside), outline ring, frame, divider, inner highlight ---
        cx2 = PL + R   # frame corner centre x
        TL = (f'<path d="M0,0H{cx2}V{PT}A{R},{R} 0 0 0 {PL},{cy2}V{CTOP}H0Z" fill="url(#{p}RT)"/>'
              f'<rect x="{cx2}" y="0" width="{W0-cx2}" height="{PT}" fill="url(#{p}T)"/>'
              f'<path d="M{PL-1},{cy2}A{R+1},{R+1} 0 0 1 {cx2},{PT-1}H{W0}V{PT}H{cx2}A{R},{R} 0 0 0 {PL},{cy2}Z" {O}/>'
              f'<path d="M{PL},{cy2}A{R},{R} 0 0 1 {cx2},{PT}H{W0}V{CTOP}H{PL}Z" {F}/>')
        if hi_a:
            TL += (f'<path d="M{PL},{cy2}A{R},{R} 0 0 1 {cx2},{PT}H{W0}V{PT+1}H{cx2}A{R-1},{R-1} 0 0 0 {PL+1},{cy2}Z" {H}/>')
        TL += f'<rect x="{PL-1}" y="{cy2}" width="1" height="{CTOP-cy2}" {O}/>'
        if hi_a:
            TL += f'<rect x="{PL}" y="{cy2}" width="1" height="{CTOP-cy2}" {H}/>'
        TL += f'<rect x="{PL}" y="{PT+TB-1}" width="{W0-PL}" height="1" {D}/>'
        # left/right column
        L = (f'<rect x="0" y="{Y_MID}" width="{PL}" height="{MID}" fill="url(#{p}L)"/>'.replace(f'y="{Y_MID}"', f'y="{Y_MID}"'))
        L = (f'<rect x="0" y="{Y_MID}" width="{PL}" height="{MID}" fill="url(#{p}L)"/>'
             f'<rect x="{PL-1}" y="{Y_MID}" width="1" height="{MID}" {O}/>'
             f'<rect x="{PL}" y="{Y_MID}" width="{W0-PL}" height="{MID}" {F}/>')
        if hi_a:
            L += f'<rect x="{PL}" y="{Y_MID}" width="1" height="{MID}" {H}/>'
        # top edge
        T = (f'<rect x="{W0}" y="0" width="{W0}" height="{PT}" fill="url(#{p}T)"/>'
             f'<rect x="{W0}" y="{PT-1}" width="{W0}" height="1" {O}/>'
             f'<rect x="{W0}" y="{PT}" width="{W0}" height="{CTOP-PT}" {F}/>')
        if hi_a:
            T += f'<rect x="{W0}" y="{PT}" width="{W0}" height="1" {H}/>'
        T += f'<rect x="{W0}" y="{PT+TB-1}" width="{W0}" height="1" {D}/>'
        C = f'<rect x="{W0}" y="{Y_MID}" width="{W0}" height="{MID}" {F}/>'
        # --- bottom row: square frame corner, separable strip shadow ---
        yb = Y_BOT
        BLc = ''
        for xi in range(0, W0, STRIP):
            y0 = yb if xi + STRIP <= PL else yb + FB
            BLc += f'<rect x="{xi}" y="{y0}" width="{STRIP}" height="{yb+CBOT-y0}" fill="url(#{p}S{xi})"/>'
        BLc += (f'<rect x="{PL-1}" y="{yb}" width="1" height="{FB+1}" {O}/>'
                f'<rect x="{PL-1}" y="{yb+FB}" width="{W0-PL+1}" height="1" {O}/>'
                f'<rect x="{PL}" y="{yb}" width="{W0-PL}" height="{FB}" {F}/>')
        B = (f'<rect x="{W0}" y="{yb}" width="{W0}" height="{FB}" {F}/>'
             f'<rect x="{W0}" y="{yb+FB}" width="{W0}" height="{PB}" fill="url(#{p}B)"/>'
             f'<rect x="{W0}" y="{yb+FB}" width="{W0}" height="1" {O}/>')
        # the left/right outline continues down the bottom-left cell's straight part
        out += [cell(f'{pre}-topleft', 0, 0, W0, CTOP, TL, off),
                cell(f'{pre}-topright', 0, 0, W0, CTOP, TL, off, True),
                cell(f'{pre}-top', W0, 0, W0, CTOP, T, off),
                cell(f'{pre}-left', 0, Y_MID, W0, MID, L, off),
                cell(f'{pre}-right', 0, Y_MID, W0, MID, L, off, True),
                cell(f'{pre}-center', W0, Y_MID, W0, MID, C, off),
                cell(f'{pre}-bottomleft', 0, yb, W0, CBOT, BLc, off),
                cell(f'{pre}-bottomright', 0, yb, W0, CBOT, BLc, off, True),
                cell(f'{pre}-bottom', W0, yb, W0, CBOT, B, off)]
    # --- hint rects (Aurorae reads the borders / shadow sizes from these) ---
    hx = 2 * SETW + 40
    h = 'fill="#000" fill-opacity="0.003"'
    out += [f'<rect id="hint-top-margin" x="{hx}" y="0" width="4" height="{PT+TB}" {h}/>',
            f'<rect id="hint-bottom-margin" x="{hx+6}" y="0" width="4" height="{PB+BB}" {h}/>',
            f'<rect id="hint-left-margin" x="{hx}" y="90" width="{PL+BL}" height="4" {h}/>',
            f'<rect id="hint-right-margin" x="{hx}" y="100" width="{PL+BL}" height="4" {h}/>',
            f'<rect id="shadow-hint-top-margin" x="{hx+20}" y="0" width="4" height="{PT}" {h}/>',
            f'<rect id="shadow-hint-bottom-margin" x="{hx+26}" y="0" width="4" height="{PB}" {h}/>',
            f'<rect id="shadow-hint-left-margin" x="{hx}" y="110" width="{PL}" height="4" {h}/>',
            f'<rect id="shadow-hint-right-margin" x="{hx}" y="120" width="{PL}" height="4" {h}/>']
    out.append('</svg>\n')
    return '\n'.join(out)

if __name__ == '__main__':
    import re
    base = 'aurorae/themes/'
    # Day: values as measured. Night: same geometry, dark fill, stronger outline + light inner edge (macOS dark look)
    day  = dict(color='#F6F6F6', div_a=0.0, outline_a=0.30, hi_a=0.0)
    night = dict(color='#2A2A2A', div_a=0.0, outline_a=0.55, hi_a=0.10)
    for name, fa, kw in (('halcyon-day-opaque', 1.0, day), ('halcyon-day-blur', 0.85, day),
                         ('halcyon-night-opaque', 1.0, night), ('halcyon-night-blur', 0.85, night)):
        open(f'{base}{name}/decoration.svg', 'w').write(build(fa, **kw))
        rc = f'{base}{name}/{name}rc'
        s = open(rc).read()
        for k, v in (('PaddingLeft', PL), ('PaddingRight', PL), ('PaddingTop', PT), ('PaddingBottom', PB)):
            s = re.sub(rf'^{k}=.*$', f'{k}={v}', s, flags=re.M)
        if name.startswith('halcyon-day'):
            s = re.sub(r'^UseTextShadow=.*$', 'UseTextShadow=false', s, flags=re.M)
        open(rc, 'w').write(s)
    print('written')
