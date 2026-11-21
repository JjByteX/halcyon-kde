# Halcyon switch for Qt Quick apps

These apps do not use the Plasma theme or the widget style for switches. They use `qqc2-desktop-style`, which draws the
switch in plain QML (`org.kde.desktop/private/SwitchIndicator.qml`) from Kirigami colours. `SwitchIndicator.qml` here is a
drop-in replacement with the same design as the Plasma-theme switch: even knob gap on all sides, grey off / accent (blue by default) on,
light and dark picked from the active colour scheme.

It has to be built into qqc2-desktop-style, since that module is compiled and cannot be overridden by dropping a file on disk.

    # use the tag that matches your installed qqc2-desktop-style / KDE Frameworks version
    git clone https://invent.kde.org/frameworks/qqc2-desktop-style.git && cd qqc2-desktop-style
    git checkout <tag>            # e.g. v6.30.0
    cp /path/to/halcyon/qt-quick/SwitchIndicator.qml org.kde.desktop/private/SwitchIndicator.qml
    cmake -B build -DCMAKE_INSTALL_PREFIX=$HOME/.local -DCMAKE_BUILD_TYPE=Release
    cmake --build build -j && cmake --install build

Make Qt find it before the system copy (path may be lib/qt6/qml), then restart the app, or log out and in:

    export QML_IMPORT_PATH=$HOME/.local/lib64/qt6/qml
    # session-wide: put that line in ~/.config/plasma-workspace/env/halcyon.sh

Tested offscreen against a stub Kirigami with the Halcyon colours (all states, light and dark).
Not tested in a real Kirigami or System Settings session. Sizes follow Kirigami.Units.gridUnit (height = 1.25 x gridUnit).
