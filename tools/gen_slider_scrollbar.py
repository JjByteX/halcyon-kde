#!/usr/bin/env python3
"""Writes plasma/desktoptheme/*/widgets/slider.svg and scrollbar.svg (Halcyon Glass).

Plasma applets and popups (volume, brightness, system tray, Kickoff ...) draw their sliders and scrollbars from these two
SVGs, not from the Qt widget style. Without them Plasma falls back to Breeze, which is why those controls looked different
from the rest of the theme. The look copies the widget style (appstyle/kstyle/breezehelper.cpp, breezemetrics.h):

  slider     4px groove, text colour at 8.5%, fully round. Fill = accent, fully round. Knob = 20x16 white pill with a soft
             0.5px-down shadow (12% black). Keyboard focus = thin accent ring hugging the knob.
  scrollbar  overlay pill, no arrows, no track. Text colour at 55%. 6px thick at rest, 10px while the pointer is over the
             bar or the pill is dragged. Light and dark follow the colour scheme.

Element contract (libplasma PlasmaComponents3/Slider.qml and ScrollBar.qml, Plasma 6):
  slider.svg     hint-handle-size, horizontal-/vertical-slider-handle|shadow|focus, groove-* and groove-highlight-* (9 pieces)
  scrollbar.svg  hint-scrollbar-size, slider-* and mouseover-slider-* (9 pieces each), background-horizontal-*/vertical-*
                 (transparent: macOS paints no track here), and the <prefix>-hint-*-inset markers.
  The QML reads the handle's padding from the inset markers (left/right = width, top/bottom = height). The resting pill has
  4px of padding on each side of a 14px bar (6px pill); the hover pill has 2px (10px pill), so the bar never changes size.
  Frame margins come from the edge pieces, so the corner radius equals the margin (3 resting, 5 on hover).

Run:  python3 tools/gen_slider_scrollbar.py
"""
import re, pathlib

root = pathlib.Path(__file__).resolve().parent.parent / 'plasma/desktoptheme'

TEXT = 'class="ColorScheme-Text" fill="currentColor"'
HIGH = 'class="ColorScheme-Highlight" fill="currentColor"'


class Sheet:
    """Lays elements out left to right in rows, each in its own box so neighbours never bleed into each other."""

    def __init__(self, width):
        self.width, self.x, self.y, self.rowh, self.out, self.maxy = width, 0, 0, 0, [], 0

    def place(self, ident, w, h, body):
        if self.x + w > self.width:
            self.x, self.y, self.rowh = 0, self.y + self.rowh + 4, 0
        x, y = self.x, self.y
        # transparent box defines the element's size for KSvg (it uses the group's bounds)
        self.out.append(f'<g id="{ident}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity="0"/>'
                        f'{body(x, y)}</g>')
        self.x += w + 4
        self.rowh = max(self.rowh, h)
        self.maxy = max(self.maxy, y + h)

    def svg(self, head):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.maxy + 4}" '
                f'viewBox="0 0 {self.width} {self.maxy + 4}">{head}\n' + '\n'.join(self.out) + '\n</svg>\n')


def rect(x, y, w, h, fill, op=1.0, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {fill} fill-opacity="{op}" {extra}/>'


def quarter(corner, x, y, r, fill, op):
    """A quarter disc of radius r filling an r x r cell at (x, y); `corner` is the cell corner the disc is rounded at."""
    d = {
        'topleft': f'M{x+r} {y} A{r} {r} 0 0 0 {x} {y+r} H{x+r} Z',
        'topright': f'M{x} {y} A{r} {r} 0 0 1 {x+r} {y+r} H{x} Z',
        'bottomleft': f'M{x} {y} A{r} {r} 0 0 0 {x+r} {y+r} V{y} Z',
        'bottomright': f'M{x+r} {y} A{r} {r} 0 0 1 {x} {y+r} V{y} Z',
    }[corner]
    return f'<path d="{d}" {fill} fill-opacity="{op}"/>'


def nine(sheet, prefix, r, fill, op):
    """9-piece fully round frame (stadium) with corner radius r: every piece is r x r."""
    for name in ('topleft', 'top', 'topright', 'left', 'center', 'right', 'bottomleft', 'bottom', 'bottomright'):
        if name in ('topleft', 'topright', 'bottomleft', 'bottomright'):
            body = lambda x, y, n=name: quarter(n, x, y, r, fill, op)
        else:
            body = lambda x, y: rect(x, y, r, r, fill, op)
        sheet.place(f'{prefix}-{name}', r, r, body)


def pill(x, y, w, h, fill, op=1.0, extra=''):
    r = min(w, h) / 2
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}" {fill} fill-opacity="{op}" {extra}/>')


# ---------------------------------------------------------------- slider
KNOB_L, KNOB_T = 20, 16            # knob length along the track, across it (Slider_ControlThickness / Slider_KnobThickness)
SHADOW_PAD = 5                     # room around the knob for its shadow
FOCUS_PAD = 3


def knob_shadow(x, y, w, h, bw, bh):
    """Stacked rounded rects, peak 12% black, 0.5px down: same approximation the widget style uses (renderSliderKnob)."""
    out, steps = '', 8
    cx, cy = x + w / 2, y + h / 2 + 0.5
    for i in range(steps, 0, -1):
        grow = 4.5 * i / steps
        out += pill(cx - bw / 2 - grow, cy - bh / 2 - grow, bw + 2 * grow, bh + 2 * grow, 'fill="#000"', 0.12 / steps)
    return out


def knob_focus(x, y, w, h, bw, bh):
    """1.5px accent ring with a 0.5px gap, drawn as an even-odd ring."""
    cx, cy = x + w / 2, y + h / 2

    def stad(ww, hh):
        r, x0, y0 = min(ww, hh) / 2, cx - ww / 2, cy - hh / 2
        return (f'M{x0+r} {y0} H{x0+ww-r} A{r} {r} 0 0 1 {x0+ww-r} {y0+hh} H{x0+r} A{r} {r} 0 0 1 {x0+r} {y0} Z')

    d = stad(bw + 4, bh + 4) + ' ' + stad(bw + 1, bh + 1)
    return f'<path d="{d}" {HIGH} fill-opacity="0.7" fill-rule="evenodd"/>'


def build_slider():
    s = Sheet(200)
    # hint-handle-size is shared by both orientations, so it is a square box that fits either knob
    s.place('hint-handle-size', KNOB_L, KNOB_L, lambda x, y: '')
    s.place('horizontal-slider-handle', KNOB_L, KNOB_T, lambda x, y: pill(x, y, KNOB_L, KNOB_T, 'fill="#fff"'))
    s.place('vertical-slider-handle', KNOB_T, KNOB_L, lambda x, y: pill(x, y, KNOB_T, KNOB_L, 'fill="#fff"'))
    hw, hh = KNOB_L + 2 * SHADOW_PAD, KNOB_T + 2 * SHADOW_PAD
    s.place('horizontal-slider-shadow', hw, hh, lambda x, y: knob_shadow(x, y, hw, hh, KNOB_L, KNOB_T))
    s.place('vertical-slider-shadow', hh, hw, lambda x, y: knob_shadow(x, y, hh, hw, KNOB_T, KNOB_L))
    fw, fh = KNOB_L + 2 * FOCUS_PAD, KNOB_T + 2 * FOCUS_PAD
    s.place('horizontal-slider-focus', fw, fh, lambda x, y: knob_focus(x, y, fw, fh, KNOB_L, KNOB_T))
    s.place('vertical-slider-focus', fh, fw, lambda x, y: knob_focus(x, y, fh, fw, KNOB_T, KNOB_L))
    # no hover element: the macOS knob does not change on hover
    nine(s, 'groove', 2, TEXT, 0.085)
    nine(s, 'groove-highlight', 2, HIGH, 1)
    return s


# ---------------------------------------------------------------- scrollbar
BAR = 14                           # bar thickness: 6px pill + 4px each side, or 10px pill + 2px each side
REST, HOVER = 6, 10                # Tokens::ScrollBar::Thickness / HoverThickness
ALPHA = 0.55                       # Tokens::ScrollBar::Alpha


def build_scrollbar():
    s = Sheet(120)
    s.place('hint-scrollbar-size', REST, REST, lambda x, y: '')
    for prefix, thick in (('slider', REST), ('mouseover-slider', HOVER)):
        nine(s, prefix, thick // 2, TEXT, ALPHA)
        pad = (BAR - thick) // 2
        # insets: left/right use the marker's width, top/bottom its height
        s.place(f'{prefix}-hint-left-inset', pad, 1, lambda x, y: '')
        s.place(f'{prefix}-hint-right-inset', pad, 1, lambda x, y: '')
        s.place(f'{prefix}-hint-top-inset', 1, pad, lambda x, y: '')
        s.place(f'{prefix}-hint-bottom-inset', 1, pad, lambda x, y: '')
    # the style paints no track behind the pill, so the hover background is fully transparent (1px pieces, no insets)
    for orient in ('horizontal', 'vertical'):
        for name in ('topleft', 'top', 'topright', 'left', 'center', 'right', 'bottomleft', 'bottom', 'bottomright'):
            s.place(f'background-{orient}-{name}', 1, 1, lambda x, y: '')
    return s


def main():
    for theme in sorted(root.iterdir()):
        head = re.search(r'<defs>.*?</defs>', (theme / 'widgets/button.svg').read_text(), re.S).group(0)
        (theme / 'widgets/slider.svg').write_text(build_slider().svg(head))
        (theme / 'widgets/scrollbar.svg').write_text(build_scrollbar().svg(head))
        print('wrote', theme.name)


if __name__ == '__main__':
    main()
