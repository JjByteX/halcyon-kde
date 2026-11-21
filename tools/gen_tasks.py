#!/usr/bin/env python3
"""Writes plasma/desktoptheme/*/widgets/tasks.svg (Halcyon Glass): the task-manager / dock button backgrounds
and the macOS-style "app is running" dot.

Run from the repo root:   python3 tools/gen_tasks.py [--button N] [--root DIR]

Backgrounds: without this file Plasma falls back to the default style's tasks.svg, which paints square, full-height cells
behind every dock icon (they showed up as a blocky band that stopped short of the rounded glass). macOS has no tiles
behind Dock icons or on hover (only a name label appears), so normal / hover / focus / minimized are fully transparent
and only 'attention' gets a soft, rounded accent tint.

Running dot: the Plasma task manager draws no running indicator of its own. Whatever tasks.svg paints for a task button
is the indicator, and launchers (pinned, not running) get no frame at all, so a dot painted into the frame shows up on running
apps only, exactly like the Dock. Same trick as WhiteSur: the frame has only top / center / bottom pieces (no corners or
left/right edges) plus the hint-stretch-borders marker, so the bottom piece is one wide tile that is stretched to the button's
width. The dot sits in the middle of that tile, so at the tile's width (--button) it is a perfect circle, and at other widths it
is only scaled by the ratio (68 -> 72px buttons make a 4px dot 4.2px wide). Pass --button with your dock's button width.
Icons-only task manager, horizontal panel:  button width = panel thickness + 6 * (Icon spacing setting, 1 by default)
(6 is the left+right frame margin, MARGIN * 2).
The dot is only painted under the 'south-' prefix, i.e. for a panel on the bottom edge; other edges stay dot-less.

Task manager asks for the prefixes  <edge>-<state>  then  <state>,  e.g. south-hover then hover, so the plain
<state> names below cover every panel edge and the south- ones add the dot for a bottom panel.
"""
import argparse, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import radii

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parent.parent / 'plasma/desktoptheme'
DEFAULT_BUTTON = 68   # width in px of one icon button (panel thickness 62 + 6)

R = radii.ATTENTION   # corner radius of the 'attention' highlight (nested in the dock: dock radius - 2)
T = 12           # height of the top/bottom slices (the dot lives in the bottom one; must be >= DOT_GAP + DOT_D)
MARGIN = 3       # content margin (hint-*-margin), in px
ROW_GAP = 3      # vertical gap between state blocks in the sheet

DOT_D = 4.0      # dot diameter, px (WhiteSur and the macOS Dock use about 4)
DOT_GAP = 5.0    # space between the dot and the bottom edge of the button, px
DOT_OPACITY = 0.9

# state -> (colour class, fill opacity); opacity 0 = fully transparent
STATES = {
    'normal':    ('ColorScheme-Text', 0),
    'minimized': ('ColorScheme-Text', 0),
    'hover':     ('ColorScheme-Text', 0),      # macOS shows only the name label on hover, no highlight
    'focus':     ('ColorScheme-Text', 0),
    'attention': ('ColorScheme-Highlight', 0.30),
}

def f(v): return '%g' % v

def round_strip(top, w, y, h):
    """Strip w x h at (0, y) with its outer two corners rounded by R (top=True: upper corners, else lower)."""
    r = R
    if top: return f'M0 {f(y+h)} L0 {f(y+r)} A{r} {r} 0 0 1 {f(r)} {f(y)} L{f(w-r)} {f(y)} A{r} {r} 0 0 1 {f(w)} {f(y+r)} L{f(w)} {f(y+h)} Z'
    return      f'M0 {f(y)} L0 {f(y+h-r)} A{r} {r} 0 0 0 {f(r)} {f(y+h)} L{f(w-r)} {f(y+h)} A{r} {r} 0 0 0 {f(w)} {f(y+h-r)} L{f(w)} {f(y)} Z'

def build(style_block, button):
    block_h = 2 * T + 1
    row = block_h + ROW_GAP
    keys = [(None, s) for s in STATES] + [('south', s) for s in STATES]   # plain names first, then south-<state>
    width, height = button + 12, len(keys) * row
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><defs>{style_block}</defs>']
    # presence of this element makes Plasma stretch (not tile) the top/bottom pieces to the button width
    out.append(f'<rect id="hint-stretch-borders" x="{button + 3}" y="0" width="1" height="1" fill="#000" fill-opacity="0"/>')
    for k, (edge, state) in enumerate(keys):
        cls, op = STATES[state]
        oy = k * row
        pre = f'{edge}-{state}' if edge else state
        for name, y, h in (('top', oy, T), ('center', oy + T, 1), ('bottom', oy + T + 1, T)):
            out.append(f'<g id="{pre}-{name}"><rect x="0" y="{y}" width="{button}" height="{h}" fill="#000" fill-opacity="0"/>')
            if op:
                if name == 'center':
                    out.append(f'<rect x="0" y="{y}" width="{button}" height="{h}" fill="currentColor" class="{cls}" fill-opacity="{f(op)}"/>')
                else:
                    out.append(f'<path d="{round_strip(name == "top", button, y, h)}" fill="currentColor" class="{cls}" fill-opacity="{f(op)}"/>')
            if edge == 'south' and name == 'bottom':
                cy = y + h - DOT_GAP - DOT_D / 2
                out.append(f'<circle cx="{f(button / 2)}" cy="{f(cy)}" r="{f(DOT_D / 2)}" fill="currentColor" class="ColorScheme-Text" fill-opacity="{f(DOT_OPACITY)}"/>')
            out.append('</g>')
        hx = button + 3
        out.append(f'<rect id="{pre}-hint-left-margin" x="{hx}" y="{oy}" width="{MARGIN}" height="1" fill="#000" fill-opacity="0"/>')
        out.append(f'<rect id="{pre}-hint-top-margin" x="{hx}" y="{oy}" width="1" height="{MARGIN}" fill="#000" fill-opacity="0"/>')
        out.append(f'<rect id="{pre}-hint-right-margin" x="{hx}" y="{oy}" width="{MARGIN}" height="1" fill="#000" fill-opacity="0"/>')
        out.append(f'<rect id="{pre}-hint-bottom-margin" x="{hx}" y="{oy}" width="1" height="{MARGIN}" fill="#000" fill-opacity="0"/>')
    out.append('</svg>\n')
    return '\n'.join(out)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--button', type=int, default=DEFAULT_BUTTON, help='width in px of one dock icon button (default %(default)s)')
    ap.add_argument('--root', type=pathlib.Path, default=DEFAULT_ROOT, help='folder that holds the halcyon-glass-* themes')
    args = ap.parse_args()
    if args.button < 2 * R + 3:
        ap.error('--button is too small')
    for theme in ('halcyon-glass-dark', 'halcyon-glass-light'):
        base = args.root / theme / 'widgets'
        style = re.search(r'<style id="current-color-scheme".*?</style>', (base / 'panel-background.svg').read_text(), re.S).group(0)
        (base / 'tasks.svg').write_text(build(style, args.button))
        print('wrote', theme, f'(button {args.button}px)')
