"""Regenerates the nine-patch drop shadow of plasma/desktoptheme/*/dialogs/background.svg.

Run from plasma/desktoptheme:   python3 ../../tools/gen_popup_shadow.py

How Plasma/KWin lay the tiles out (this is what the old version got wrong):
  * the shadow is 8 tiles (+ an empty centre) around the window; the corner tiles keep their own size and the four
    edge tiles (1px wide/high) are stretched between them
  * shadow-hint-*-margin = how far the shadow reaches OUTSIDE the window on each side
  * a tile that is bigger than its margin reaches INTO the window by (size - margin)

Rules that keep it clean:
  1. every corner tile must reach into the window by INNER px, on all four corners. The old bottom tiles reached 0px, so the
     rounded bottom corners had nothing behind them (the visible square).
  2. INNER must be >= ~2.5 sigma, so the corner tile has converged to the straight-edge profile where it meets the stretched
     edge tile. With the old sigma 27 / 18px overlap the two disagreed by ~25% -> a visible seam.
  3. the shadow is NOT cut out along the window edge (only well inside it), so anti-aliased corner pixels never show a gap.
"""
import re, io, base64, numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

# Same shadow as the Qt menus (Tokens::Menu in appstyle/kstyle/breezemetrics.h: dy 8, sigma 24, black 25%), in both themes, so a Plasma popup
# and a Qt menu side by side cast the same shadow. No tight contact shadow: the 1px outline of the frame does that job.
SIG, DY = 24.0, 8            # blur sigma, downward offset
CSIG, CDY, CALPHA = 2.5, 1, 0.0   # contact shadow: off
ALPHA = {'dark': 0.25, 'light': 0.25}
L, T, R, B = 56, 48, 56, 64  # reach outside the window (shadow-hint margins): ~2.3 sigma, minus dy on top and plus dy at the bottom
INNER = 40                   # how far each corner tile reaches into the window. Where it meets the stretched edge tile the corner and edge profiles differ by <1% alpha (>= 1.6 sigma)
CUT = 3                      # shadow is removed this far inside the window edge (never at the edge itself)
X0 = 300                     # where the tiles sit in the svg
WIN = 300                    # window size used while rendering (large enough that the middle is straight)


def make(rad, alpha):
    SS = 4
    W, H = L + WIN + R, T + WIN + B
    def mask(inset, r):
        im = Image.new('L', (W * SS, H * SS), 0)
        ImageDraw.Draw(im).rounded_rectangle([(L + inset) * SS, (T + inset) * SS, (L + WIN - inset) * SS - 1, (T + WIN - inset) * SS - 1],
                                             radius=max(r, 0) * SS, fill=255)
        return np.asarray(im.resize((W, H), Image.LANCZOS), dtype=float) / 255
    M = mask(0, rad)
    a1 = alpha * gaussian_filter(np.roll(M, DY, axis=0), SIG)
    a2 = CALPHA * gaussian_filter(np.roll(M, CDY, axis=0), CSIG)
    a = 1 - (1 - a1) * (1 - a2)
    a = a * (1 - mask(CUT, rad - CUT))          # clear only well inside the window
    a[a < 0.5 / 255] = 0
    return a


def png(a):
    arr = np.zeros(a.shape + (4,), dtype=np.uint8)
    arr[..., 3] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    b = io.BytesIO(); Image.fromarray(arr, 'RGBA').save(b, 'PNG', optimize=True)
    return base64.b64encode(b.getvalue()).decode()


def group(a):
    H, W = a.shape; mx, my = W // 2, H // 2
    lw, rw, th, bh = L + INNER, R + INNER, T + INNER, B + INNER
    cells = {
        'topleft':     (a[:th, :lw],            X0,           0),
        'top':         (a[:th, mx:mx + 1],      X0 + lw,      0),
        'topright':    (a[:th, W - rw:],        X0 + lw + 1,  0),
        'left':        (a[my:my + 1, :lw],      X0,           th),
        'center':      (np.zeros((1, 1)),       X0 + lw,      th),
        'right':       (a[my:my + 1, W - rw:],  X0 + lw + 1,  th),
        'bottomleft':  (a[H - bh:, :lw],        X0,           th + 1),
        'bottom':      (a[H - bh:, mx:mx + 1],  X0 + lw,      th + 1),
        'bottomright': (a[H - bh:, W - rw:],    X0 + lw + 1,  th + 1)}
    out = ''
    for n, (c, x, y) in cells.items():
        h, w = c.shape
        out += (f'<g id="shadow-{n}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>'
                f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none" '
                f'xlink:href="data:image/png;base64,{png(c)}"/></g>\n')
    return out, X0 + lw + 1 + rw, th + 1 + bh


def main():
  for theme in ['halcyon-glass-light', 'halcyon-glass-dark']:
    p = f'{theme}/dialogs/background.svg'
    s = open(p).read()
    m = re.search(r'rx="([\d.]+)"', s) or re.search(r'A([\d.]+) [\d.]+ 0 0 [01] ', s)
    rad = float(m.group(1)) if m else 6.0
    g, cw, ch = group(make(rad, ALPHA['light' if 'light' in theme else 'dark']))
    s = re.sub(r'<g id="shadow-(?!hint)\w+">.*?</g>\n?', '', s, flags=re.S)
    for i, (w, h) in {'left': (L, 1), 'top': (1, T), 'right': (R, 1), 'bottom': (1, B)}.items():
        s = re.sub(rf'(<rect id="shadow-hint-{i}-margin" x=")[^"]*(" y=")[^"]*(" width=")[^"]*(" height=")[^"]*"',
                   rf'\g<1>88\g<2>0\g<3>{w}\g<4>{h}"', s)
    s = s.replace('</svg>', g + '</svg>')
    cw, ch = max(cw, 446), max(ch, 146)
    s = re.sub(r'(<svg [^>]*?)width="\d+" height="\d+" viewBox="0 0 \d+ \d+">',
               rf'\g<1>width="{cw}" height="{ch}" viewBox="0 0 {cw} {ch}">', s, count=1)
    open(p, 'w').write(s)
    print(p, 'radius', rad, 'canvas', cw, ch, len(s) // 1024, 'KB')

if __name__ == '__main__':
    main()
