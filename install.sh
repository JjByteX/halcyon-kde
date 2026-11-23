#!/usr/bin/env bash
# Installs Halcyon (window decorations, Halcyon Glass Plasma style, colour schemes, the Night/Day global themes and the
# Halcyon Glass application style) into your user directories. No root needed. Safe to re-run.
#   ./install.sh              install everything; build the application style if the build tools are present
#   ./install.sh --no-style   skip the application style (the global themes then use Breeze for widgets)
#   ./install.sh --no-qtquick skip the Qt Quick switch (System Settings, Discover keep the Breeze toggle)
#   ./install.sh --no-icons   leave your icon theme alone (otherwise Night/Day use Papirus-Dark/Papirus-Light when installed)
#   ./install.sh --dock-button N   centre the running-app dot for a dock whose icon buttons are N px wide (default 68; see README)
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dest="${XDG_DATA_HOME:-$HOME/.local/share}"
cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
prefix="${HALCYON_PREFIX:-$HOME/.local}"
mkdir -p "$dest/aurorae/themes" "$dest/plasma/desktoptheme" "$dest/plasma/look-and-feel" "$dest/color-schemes"
cp -r "$here"/aurorae/themes/halcyon-*          "$dest/aurorae/themes/"
# the -opaque variants share their button SVGs with the -blur variants (only decoration.svg and the rc differ)
for v in day night; do
    for f in close minimize maximize restore alldesktops keepabove keepbelow; do
        cp "$dest/aurorae/themes/halcyon-$v-blur/$f.svg" "$dest/aurorae/themes/halcyon-$v-opaque/$f.svg"
    done
done
cp -r "$here"/plasma/desktoptheme/halcyon-glass-* "$dest/plasma/desktoptheme/"
cp -r "$here"/look-and-feel/org.jjbytex.halcyon.* "$dest/plasma/look-and-feel/"
cp    "$here"/color-schemes/Halcyon*.colors      "$dest/color-schemes/"

# the running-app dot in tasks.svg only lines up at one button width, so rebuild it for the width the user gave
dock_button=""
args=("$@")
for i in "${!args[@]}"; do
    case "${args[$i]}" in
        --dock-button=*) dock_button="${args[$i]#--dock-button=}" ;;
        --dock-button)   dock_button="${args[$((i+1))]:-}" ;;
    esac
done
if [[ -n "$dock_button" ]]; then
    if [[ "$dock_button" =~ ^[0-9]+$ ]] && command -v python3 >/dev/null 2>&1 \
       && python3 "$here/tools/gen_tasks.py" --button "$dock_button" --root "$dest/plasma/desktoptheme" >/dev/null; then
        echo "Dock dot centred for ${dock_button}px buttons"
    else
        echo "Could not rebuild the dock dot for '$dock_button' (needs a number and python3); using the default width."
    fi
fi
echo "Installed themes to $dest"

# Icons: Night uses Papirus-Dark and Day uses Papirus-Light. Papirus is not bundled, so a global theme only switches to it
# if it is installed; otherwise the icon line is dropped and your current icons stay.
icon_theme_found() {
    local d data_dirs
    IFS=: read -ra data_dirs <<<"${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
    for d in "$dest/icons" "$HOME/.icons" "${data_dirs[@]/%//icons}"; do
        [[ -d "$d/$1" ]] && return 0
    done
    return 1
}
missing_icons=()
for pair in night:Papirus-Dark day:Papirus-Light; do
    defaults="$dest/plasma/look-and-feel/org.jjbytex.halcyon.${pair%%:*}/contents/defaults"
    if [[ " $* " != *" --no-icons "* ]] && icon_theme_found "${pair#*:}"; then
        echo "Icons: ${pair%%:*} uses ${pair#*:}"
    else
        sed -i '/^\[kdeglobals\]\[Icons\]$/,/^$/d' "$defaults"
        [[ " $* " != *" --no-icons "* ]] && missing_icons+=("${pair#*:}")
    fi
done
if [[ ${#missing_icons[@]} -gt 0 ]]; then
    echo "Papirus not found (${missing_icons[*]}), so those themes keep your current icons."
    echo "Install the papirus-icon-theme package (pacman, dnf, apt and zypper all call it that), then run ./install.sh again."
fi

style_ok=0
if [[ " $* " != *" --no-style "* ]]; then
    if command -v cmake >/dev/null 2>&1 && { command -v make >/dev/null 2>&1 || command -v ninja >/dev/null 2>&1; }; then
        build="$(mktemp -d)"
        echo "Building the Halcyon Glass application style (needs Qt 6 and KDE Frameworks 6 development packages)..."
        if cmake -S "$here/appstyle" -B "$build" -DCMAKE_INSTALL_PREFIX="$prefix" -DCMAKE_BUILD_TYPE=Release >"$build/cmake.log" 2>&1 \
           && cmake --build "$build" -j"$(nproc)" >>"$build/cmake.log" 2>&1 \
           && cmake --install "$build" >>"$build/cmake.log" 2>&1; then
            style_ok=1
            echo "Application style installed under $prefix"
        else
            echo "The application style did not build. Log: $build/cmake.log"
            echo "--- last errors ---"
            grep -iE -B1 -A3 "error|not found" "$build/cmake.log" | tail -n 25 || true
            echo "-------------------"
            echo "Themes are still installed and use Breeze for widgets. Install the Qt 6 / KF6 -devel packages and re-run to add it."
        fi
    else
        echo "cmake/make not found, skipping the application style. Themes use Breeze for widgets."
    fi
fi

envlines=""
qq_ok=0
if [[ " $* " != *" --no-qtquick "* ]]; then
    # System Settings, Discover etc. draw switches in QML via qqc2-desktop-style, a compiled module, so the Halcyon
    # SwitchIndicator.qml has to be built into a private copy of it that Qt finds first (see qt-quick/README.md)
    if command -v git >/dev/null 2>&1 && command -v cmake >/dev/null 2>&1; then
        ver="$(pkg-config --modversion KF6Config 2>/dev/null || true)"
        src="$(mktemp -d)"; qlog="$src/build.log"
        echo "Building the Halcyon switch for Qt Quick apps (qqc2-desktop-style ${ver:-unknown version}, needs network)..."
        if { git clone -q --depth 1 ${ver:+--branch "v$ver"} https://invent.kde.org/frameworks/qqc2-desktop-style.git "$src/q" \
                || git clone -q --depth 1 https://invent.kde.org/frameworks/qqc2-desktop-style.git "$src/q"; } >"$qlog" 2>&1 \
           && cp "$here/qt-quick/SwitchIndicator.qml" "$src/q/org.kde.desktop/private/SwitchIndicator.qml" \
           && cmake -S "$src/q" -B "$src/b" -DCMAKE_INSTALL_PREFIX="$prefix" -DCMAKE_BUILD_TYPE=Release >>"$qlog" 2>&1 \
           && cmake --build "$src/b" -j"$(nproc)" >>"$qlog" 2>&1 \
           && cmake --install "$src/b" >>"$qlog" 2>&1; then
            qmldir="$(find "$prefix" -type d -path '*/qml/org/kde/desktop' -printf '%h\n' 2>/dev/null | head -n1 || true)"
            qmldir="${qmldir%/org/kde}"
            if [[ -n "$qmldir" ]]; then
                qq_ok=1
                envlines+="export QML_IMPORT_PATH=\"$qmldir\${QML_IMPORT_PATH:+:\$QML_IMPORT_PATH}\"\n"
                echo "Qt Quick switch installed under $qmldir"
            fi
        else
            echo "The Qt Quick switch did not build. Log: $qlog"
            tail -n 15 "$qlog" || true
            echo "Everything else is installed. Qt Quick apps keep the Breeze toggle."
        fi
    else
        echo "git/cmake not found, skipping the Qt Quick switch."
    fi
fi

if [[ $style_ok -eq 1 || $qq_ok -eq 1 ]]; then
    mkdir -p "$cfg/plasma-workspace/env"
    : >"$cfg/plasma-workspace/env/halcyon.sh"   # rewritten on every run, so no duplicate lines
fi
if [[ $qq_ok -eq 1 ]]; then
    printf '%b' "$envlines" >>"$cfg/plasma-workspace/env/halcyon.sh"
fi

if [[ $style_ok -eq 1 ]]; then
    # Qt only looks for style plugins in its own directories, so point it at the install prefix at every login
    plugdir="$(find "$prefix" -type f -name 'halcyonglass6.so' -printf '%h\n' 2>/dev/null | head -n1 || true)"
    plugdir="${plugdir%/styles}"
    if [[ -n "$plugdir" ]]; then
        printf 'export QT_PLUGIN_PATH="%s${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"\n' "$plugdir" >>"$cfg/plasma-workspace/env/halcyon.sh"
        echo "Plugin path set for login: $plugdir"
    fi
    # only now that the style exists do the global themes switch widgets to it
    for d in "$dest"/plasma/look-and-feel/org.jjbytex.halcyon.*/contents/defaults; do
        sed -i 's/^widgetStyle=.*/widgetStyle=HalcyonGlass/' "$d"
    done
    echo "Log out and in once so the style is picked up."
fi
[[ $qq_ok -eq 1 ]] && echo "Log out and in once so Qt Quick apps pick up the new switch."
echo "Apply it in System Settings > Colors & Themes > Global Theme (Halcyon Night / Halcyon Day),"
echo "or from a terminal:  plasma-apply-lookandfeel -a org.jjbytex.halcyon.night"
