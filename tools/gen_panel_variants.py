#!/usr/bin/env python3
"""Writes the opaque/ and translucent/ variants (panel, popups, tooltips / dock labels) of the Halcyon Glass Plasma styles.

Run from the repo root:   python3 tools/gen_panel_variants.py [dialogs]   (with 'dialogs' only the dialog backgrounds are rewritten)
Re-run it after changing widgets/panel-background.svg, widgets/tooltip.svg or dialogs/background.svg (tools/gen_panel_frame.py, gen_alert.py and gen_popup_shadow.py write those).
The radii come from tools/radii.py.

Why: Plasma only offers the panel Opacity choices (Adaptive / Opaque / Translucent) when the style turns on
[AdaptiveTransparency] in its plasmarc AND ships opaque/ and translucent/ copies of the panel and dialog backgrounds.
  opaque/        solid copy of the base files (used when a window touches the panel, or Opacity = Opaque)
  translucent/   same shapes, but the body fill is see-through so KWin's blur shows through, like macOS's glass menu bar
The edge ring and top highlight are left alone so the glass edge stays crisp.

Shadow: the base files let each shadow tile reach UNDER the window edge (so rounded corners never show a gap). That is
invisible while the body is solid, but with a see-through body it shows as a thick dark frame inside the glass. So for
translucent/ the shadow tiles are re-rendered as PNGs with everything under the window made transparent (the little
gaps at the rounded corners are kept). Needs:  pip install cairosvg pillow  (only to run this script, not to use the theme)
"""
import base64, io, math, pathlib, re, sys
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import radii

import cairosvg
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent / 'plasma/desktoptheme'

# fill alpha of the body, per theme: (panel, dialogs/popups, tooltips / dock labels)
ALPHA = {
    'halcyon-glass-dark':  (0.58, 0.80, 0.70),
    'halcyon-glass-light': (0.62, 0.72, 0.74),
}

TAG = re.compile(r'<(?:path|rect)\b[^>]*class="ColorScheme-Background"[^>]*/>')

def set_body_alpha(svg: str, alpha=None) -> str:
    """Give every body tile fill-opacity=alpha (replacing any alpha the base had); None = fully solid."""
    def fix(m):
        tag = re.sub(r' fill-opacity="[^"]*"', '', m.group(0))
        return tag if alpha is None else tag[:-2] + f' fill-opacity="{alpha}"/>'
    out, n = TAG.subn(fix, svg)
    assert n == 9, f"expected 9 body tiles, found {n}"   # 8 frame tiles + centre
    return out


CORNER_R = radii.SURFACE   # default window corner radius for the shadow cut (the callers below pass the real one, from tools/radii.py)
SHADOW_G = re.compile(r'<g id="shadow-(?P<name>topleft|top|topright|left|right|bottomleft|bottom|bottomright)">(?P<body>.*?)</g>', re.S)

def _margin(svg, side):
    attr = 'width' if side in ('left', 'right') else 'height'
    return float(re.search(rf'id="shadow-hint-{side}-margin"[^>]*?\b{attr}="([\d.]+)"', svg).group(1))

def cut_shadow_under_window(svg: str, scale: int, radius: float = CORNER_R) -> str:
    """Make every shadow tile transparent where it overlaps the window, keeping the rounded-corner gaps.

    The window is a rounded rectangle, so the part to clear is exactly that shape. Its coverage is measured per pixel with 8x8
    supersampling and the shadow alpha is multiplied by (1 - coverage): edge pixels end up part shadow, part clear, which blends
    with the antialiased edge of the body. A hard on/off cut left a sawtooth of un-darkened backdrop along the corner arcs."""
    ml, mt, mr, mb = (_margin(svg, k) for k in ('left', 'top', 'right', 'bottom'))
    sheet = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert('RGBA')
    SS, BIG = 8, 200

    def repl(m):
        name, body = m.group('name'), m.group('body')
        x, y, w, h = (float(v) for v in re.search(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', body).groups())
        # the window rectangle in tile-local units; sides the tile does not touch run far past it (no corner there)
        x0 = ml if 'left' in name else -BIG
        x1 = w - mr if 'right' in name else w + BIG
        y0 = mt if 'top' in name else -BIG
        y1 = h - mb if 'bottom' in name else h + BIG
        tile = sheet.crop((round(x * scale), round(y * scale), round((x + w) * scale), round((y + h) * scale)))
        k = scale * SS
        mask = Image.new('L', (tile.width * SS, tile.height * SS), 0)
        ImageDraw.Draw(mask).rounded_rectangle([x0 * k, y0 * k, x1 * k - 1, y1 * k - 1], radius=radius * k, fill=255)
        cov = np.asarray(mask.resize(tile.size, Image.BOX), dtype=float) / 255
        arr = np.asarray(tile).astype(float)
        arr[..., 3] *= (1 - cov)
        tile = Image.fromarray(np.clip(arr + 0.5, 0, 255).astype(np.uint8), 'RGBA')
        buf = io.BytesIO(); tile.save(buf, 'PNG', optimize=True)
        uri = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
        box = re.search(r'<rect (x="[\d.]+" y="[\d.]+" width="[\d.]+" height="[\d.]+")', body).group(1)
        return (f'<g id="shadow-{name}"><rect {box} fill="#000" fill-opacity="0"/>'
                f'<image {box} preserveAspectRatio="none" xlink:href="{uri}"/></g>')

    out, n = SHADOW_G.subn(repl, svg)
    assert n == 8, f'expected 8 shadow tiles, found {n}'
    if 'xmlns:xlink' not in out:
        out = out.replace('<svg xmlns="http://www.w3.org/2000/svg"', '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"', 1)
    return out

for theme, (a_panel, a_dialog, a_tip) in ALPHA.items():
    base = ROOT / theme
    # (folder, file, translucent alpha, window corner radius, shadow raster scale)
    for sub, rel, alpha, radius, scale in (('widgets', 'panel-background.svg', a_panel, radii.DOCK, 2),
                                           ('dialogs', 'background.svg', a_dialog, radii.DIALOG, 1),
                                           ('widgets', 'tooltip.svg', a_tip, radii.LABEL, 2)):
        if sys.argv[1:] == ['dialogs'] and sub != 'dialogs':
            continue
        src = (base / sub / rel).read_text()
        for variant in ('opaque', 'translucent'):
            dst = base / variant / sub / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if variant == 'opaque':
                dst.write_text(set_body_alpha(src, None))
            else:
                dst.write_text(cut_shadow_under_window(set_body_alpha(src, alpha), scale, radius))
    if sys.argv[1:] == ['dialogs']:
        print('wrote dialogs of', theme)
        continue
    # turn on the Adaptive / Opaque / Translucent panel choice and give the blurred glass a little macOS-style vibrancy
    (base / 'plasmarc').write_text(
        '[AdaptiveTransparency]\nenabled=true\n\n'
        '[BlurBehindEffect]\nenabled=true\n\n'
        '[ContrastEffect]\nenabled=true\ncontrast=0.2\nintensity=1.0\nsaturation=1.6\n')
    print('wrote', theme)
