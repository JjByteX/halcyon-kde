"""Renders the macOS-style traffic-light buttons (14px circles) to RGBA images.

Browsers cannot draw that SVG correctly: its filters use the `plus-lighter` blend (not valid in feBlend) and
`feMorphology` for the inner-shadow "spread", which dilates a circle into an octagon. Chromium therefore shows black-topped
octagons. This module redraws the same filter chain with the original semantics (circular spread, plus-lighter = add):

  1. drop shadow      dy 1.5, blur 0.5, 15% of the button's own tint, outside the shape
  2. fill             #FA9891 / #FFDA66 / #ADE392
  3. inner shadow     spread 5, dy 11, blur 4.5, black, OVERLAY    (alpha 0.55 / 1 / 0.94 per button)
  4. inner shadow     spread 5, dy  5, blur 2,   grey,  PLUS-LIGHTER
  5. inner shadow     blur 0.5, no offset, 40% dark tint (thin rim)
  6/7. inner shadow   spread 1.5, dx +2 / -2, blur 0.125, dark tint (left and right slivers)
"""
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image

S = 16                       # supersampling per css px
W, H = 18, 20                # cell in css px: 2px side margin, room below for the drop shadow
BX, BY, R = 2.0, 0.5, 7.0    # circle box top-left and radius (14x14, rx 7)
CX, CY = BX + R, BY + R

BTN = {
    'close': dict(fill=(0xFA, 0x98, 0x91), drop=(0.980392, 0.505882, 0.470588), a2=0.55, i3=0.101961, rim=(0.768627, 0, 0)),
    'min':   dict(fill=(0xFF, 0xDA, 0x66), drop=(1, 0.843137, 0.34902),         a2=1.00, i3=0.0509804, rim=(0.619608, 0.0392157, 0)),
    'max':   dict(fill=(0xAD, 0xE3, 0x92), drop=(0.678431, 0.890196, 0.572549), a2=0.94, i3=0.0509804, rim=(0, 0.337255, 0)),
}

_yy, _xx = np.mgrid[0:H * S, 0:W * S]
_px, _py = (_xx + 0.5) / S, (_yy + 0.5) / S


def _disc(r, dx=0.0, dy=0.0):
    return (np.hypot(_px - CX - dx, _py - CY - dy) <= r).astype(np.float64)


def _blur(a, sd):
    return gaussian_filter(a, sd * S, mode='constant') if sd > 0 else a


def render(name, rims=True):
    """Returns the premultiplied RGBA float array at S x resolution."""
    p = BTN[name]
    hard = _disc(R)
    inner = lambda spread, dx, dy, sd: np.clip(hard - _blur(_disc(R + spread, dx, dy), sd), 0, 1)
    out = np.zeros((H * S, W * S, 4))

    def over(rgb, a):
        a = a[..., None]
        out[..., :3] = np.array(rgb, float) * a + out[..., :3] * (1 - a)
        out[..., 3:] = a + out[..., 3:] * (1 - a)

    over(p['drop'], np.clip(_blur(_disc(R, 0, 1.5), 0.5) - hard, 0, 1) * 0.15)
    over([c / 255 for c in p['fill']], hard)
    inside = hard[..., None] > 0
    # overlay blend of black over the (opaque) shape: base <= .5 -> 0, else 1 - 2(1-base)
    a = (inner(5, 0, 11, 4.5) * p['a2'])[..., None]
    b = out[..., :3]
    ov = np.where(b <= 0.5, 0.0, 1 - 2 * (1 - b))
    out[..., :3] = np.where(inside, b * (1 - a) + ov * a, b)
    # plus-lighter: add the grey, weighted by the shadow's alpha
    a = inner(5, 0, 5, 2)[..., None]
    out[..., :3] = np.where(inside, np.clip(out[..., :3] + p['i3'] * a, 0, 1), out[..., :3])
    if rims:
        over(p['rim'], inner(0, 0, 0, 0.5) * 0.4 * hard)
        for dx in (2, -2):
            over(p['rim'], inner(1.5, dx, 0, 0.125) * hard)
    return out


def to_image(prem, per_px=8):
    f = S // per_px
    h, w = prem.shape[:2]
    d = prem.reshape(h // f, f, w // f, f, 4).mean(axis=(1, 3))
    a = d[..., 3:]
    rgb = np.where(a > 1e-6, d[..., :3] / np.maximum(a, 1e-6), 0)
    arr = np.concatenate([rgb, a], axis=2)
    return Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA')


if __name__ == '__main__':
    sheet = Image.new('RGBA', (W * 8 * 3, H * 8), (255, 255, 255, 255))
    for i, n in enumerate(BTN):
        sheet.alpha_composite(to_image(render(n)), (i * W * 8, 0))
    sheet.save('buttons_preview.png')
