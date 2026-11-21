#!/usr/bin/env python3
"""Corner radii for Halcyon: one place that says which radius each kind of surface uses.

Halcyon is macOS-inspired but keeps its own, tighter radii. It does NOT follow macOS values (the real Dock, menus
and alerts are much rounder). Radius follows the ROLE of a shape, not the file it happens to live in:

  CONTROL (6)   buttons, fields, tabs, and small pieces that sit inside a surface. Also small floating labels
                (tooltips, dock labels).
  SURFACE (10)  anything that floats or frames content: windows, dialogs and popups, menus, alerts, the dock.

Nesting rule: a shape inside a rounded surface gets a smaller radius, inner = outer - padding (see inner()), so the
curves stay concentric. A nested shape must never be rounder than the surface around it.

Generators import their radius from here; do not type a radius into a generator. The C++ style cannot import this file,
so its two constants are checked instead:

    python3 tools/radii.py --check        (run from the repo root; exits 1 on a mismatch)

Known exceptions (listed so they are decisions, not accidents):
  ROW          12px list/view rows (tools/gen_nine_patch.py). Rounder than SURFACE, so it breaks the nesting rule.
               Left as it was; changing it is a visual redesign, not a cleanup.
  WIDGET_CARD  6px, plasma widgets/background.svg. Not generated here (the light one carries extra hairline shapes),
               and where Plasma uses it has not been confirmed, so its tier is undecided.
  Checkbox 4px and Frame_FrameRadius 5 in breezemetrics.h are geometry for tiny parts, not tiers.
"""
import pathlib, re, sys

CONTROL = 6
SURFACE = 10

# role -> radius
DOCK = SURFACE        # panel / dock background (plasma widgets/panel-background.svg)
DIALOG = SURFACE      # Plasma dialogs, popups, notifications (dialogs/background.svg), Qt alerts
WINDOW = SURFACE      # Aurorae window decoration (top corners; KWin cannot round the bottom of a client)
MENU = SURFACE        # Qt menus (Tokens::Menu)
LABEL = CONTROL       # tooltips and dock labels (plasma widgets/tooltip.svg)
TAB = CONTROL         # Qt tabs

ROW = 12              # exception, see above
WIDGET_CARD = 6       # exception, see above


def inner(outer, padding):
    """Radius for a shape inset by `padding` px inside a surface of radius `outer` (never below 0)."""
    return max(outer - padding, 0)


ATTENTION = inner(DOCK, 2)   # dock "attention" tint, inside the dock (tools/gen_tasks.py): 8


# ---- check -----------------------------------------------------------------------------------------------------

def _arc_radius(svg_path):
    """Radius of the first corner arc in a plasma nine-patch svg (the 'topleft' piece), or None."""
    s = pathlib.Path(svg_path).read_text()
    m = re.search(r'<g id="topleft">.*?A\s*([\d.]+)\s+[\d.]+\s+0\s+0\s+[01]', s, re.S)
    return float(m.group(1)) if m else None


def check(root='.'):
    root = pathlib.Path(root)
    bad = []

    # C++ metrics
    h = (root / 'appstyle/kstyle/breezemetrics.h').read_text()
    for name, want in (('Control_Radius', CONTROL), ('Surface_Radius', SURFACE), ('TabBar_TabRadius', TAB)):
        m = re.search(rf'\b{name}\s*=\s*(\d+)\s*;', h)
        got = int(m.group(1)) if m else None
        print(f'  breezemetrics.h  {name:<18} {got}  (want {want})')
        if got != want:
            bad.append(name)

    # shipped plasma pieces
    for theme in ('halcyon-glass-dark', 'halcyon-glass-light'):
        base = root / 'plasma/desktoptheme' / theme
        for sub, want, what in (('widgets/panel-background.svg', DOCK, 'dock'),
                                ('widgets/tooltip.svg', LABEL, 'label'),
                                ('dialogs/background.svg', DIALOG, 'dialog')):
            got = _arc_radius(base / sub)
            print(f'  {theme:<20} {sub:<30} {got}  (want {want}, {what})')
            if got is None or abs(got - want) > 0.01:
                bad.append(f'{theme}/{sub}')
    if bad:
        print('MISMATCH:', ', '.join(bad)); return 1
    print('radii in sync')
    return 0


if __name__ == '__main__':
    if '--check' in sys.argv[1:]:
        sys.exit(check(next((a for a in sys.argv[1:] if not a.startswith('-')), '.')))
    print(__doc__)
    for k in ('CONTROL', 'SURFACE', 'DOCK', 'DIALOG', 'WINDOW', 'MENU', 'LABEL', 'TAB', 'ATTENTION', 'ROW', 'WIDGET_CARD'):
        print(f'  {k:<12} {globals()[k]}')
