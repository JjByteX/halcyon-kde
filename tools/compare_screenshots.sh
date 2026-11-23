#!/usr/bin/env bash
# Before/after screenshots: stock Breeze vs Halcyon, from your live Plasma 6 session.
# Real screenshots only, nothing is drawn or mocked up.
#
# Press Alt+F2 and run
#     ~/Downloads/halcyon/tools/compare_screenshots.sh
# Nothing else to do: no windows to open, nothing to click (and no terminal window ends up in the shots).
# A notification says when it is done, about a minute later.
#
# It switches to Breeze and takes the shots, switches to Halcyon and takes the same shots, and joins each pair.
# The scenes (all set up by the script):
#     settings      the whole desktop with System Settings open on its start page, Quick Settings (full screen, not cropped;
#                   SETTINGS_PAGE=kcm_nightlight opens another page)
#     controls      a showcase window: buttons, switches, checkboxes, radio buttons, sliders, tabs, a list
#     titlebar      close-up of that window's title bar and window buttons (Breeze above, Halcyon below)
#     menu          the same window with a menu open
#     combo         the same window with a drop-down list open
#     volume        the volume overlay
#     launcher      the application launcher
#     notification  a sample notification
#
#   tools/compare_screenshots.sh [night|day] [scene[=WxH+X+Y] ...]
#
# Extra scenes: `desktop` takes whatever is on screen as it is (your own windows, the dock). Any other name is a
# manual scene: the script counts down so you can set it up yourself before each shot.
#   tools/compare_screenshots.sh night controls menu desktop
#
# Output: docs/screenshots/compare-<night|day>-<scene>.png. Every image is Breeze on the left and Halcyon on the right,
# cropped to the window or popup (the same area on both sides). Scenes that fail on either side are skipped, never half done.
#
# Env:  START=5   seconds before the first shot (time to let KRunner close or to move a terminal away)
#       WAIT=4    seconds to let the desktop settle after a theme switch
#       COUNT=8   seconds to set up each manual scene
#       CROP=WxH+X+Y   fixed crop for every scene (instead of the automatic one)
#       PAD=28    pixels of room around the window in the automatic crop
#       KEEP_RAW=1   also keep the two cropped single shots in docs/screenshots/raw/
#       TITLEBAR_H=120   height in pixels of the title bar close-up
#
# Needs: spectacle, ImageMagick (magick or convert), plasma-apply-lookandfeel, kreadconfig6.
# For the automatic scenes: the Qt 6 `qml` tool (qt6-declarative; set QML=/path/to/qml if it isn't found) for the showcase window; notify-send; qdbus6/qdbus/gdbus. Your theme is restored at the end.
set -euo pipefail

variant=night
case "${1:-}" in night|day) variant="$1"; shift ;; esac

case "$variant" in
    night) breeze_id="org.kde.breezedark.desktop"; halcyon_id="org.jjbytex.halcyon.night"; breeze_label="Breeze Dark"; halcyon_label="Halcyon Night" ;;
    day)   breeze_id="org.kde.breeze.desktop";     halcyon_id="org.jjbytex.halcyon.day";   breeze_label="Breeze";      halcyon_label="Halcyon Day" ;;
esac

names=(); crops=()
if [ $# -eq 0 ]; then set -- settings controls titlebar menu combo volume launcher notification; fi
for arg in "$@"; do
    n="${arg%%=*}"; c="${CROP:-}"; [[ "$arg" == *=* ]] && c="${arg#*=}"
    [[ "$n" =~ ^[a-z0-9_-]+$ ]] || { echo "scene names: lowercase letters, digits, - and _ only ('$n')" >&2; exit 2; }
    names+=("$n"); crops+=("$c")
done
start_s="${START:-5}"; wait_s="${WAIT:-4}"; count="${COUNT:-8}"

for cmd in spectacle plasma-apply-lookandfeel kreadconfig6; do
    command -v "$cmd" >/dev/null || { echo "missing: $cmd" >&2; exit 1; }
done
if command -v magick >/dev/null; then IM=(magick); IDENT=(magick identify)
elif command -v convert >/dev/null && command -v identify >/dev/null; then IM=(convert); IDENT=(identify)
else echo "missing: ImageMagick (magick or convert)" >&2; exit 1; fi

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$root/docs/screenshots"; mkdir -p "$out"

notify() { echo "$*"; if command -v notify-send >/dev/null; then notify-send -t "${2:-4000}" "Halcyon screenshots" "$1" || true; fi; }

original="$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage || true)"
tmp="$(mktemp -d)"
finish() {
    local rc=$?
    rm -rf "$tmp"
    [ -n "$original" ] && plasma-apply-lookandfeel -a "$original" >/dev/null 2>&1 || true
    if [ $rc -ne 0 ]; then notify "Failed (exit $rc). Run it from a terminal to see why." 8000; fi
}
trap finish EXIT

dbus_call() {   # dbus_call <path> <interface.method> [args...]  (on org.kde.plasmashell)
    local path="$1" method="$2"; shift 2
    if   command -v qdbus6 >/dev/null; then qdbus6 org.kde.plasmashell "$path" "$method" "$@" >/dev/null
    elif command -v qdbus  >/dev/null; then qdbus  org.kde.plasmashell "$path" "$method" "$@" >/dev/null
    elif command -v gdbus  >/dev/null; then gdbus call --session --dest org.kde.plasmashell --object-path "$path" --method "$method" "$@" >/dev/null
    else return 1; fi
}

# Find a working Qt 6 `qml`. A plain `qml` is often the Qt 4/5 qtchooser wrapper, so it is tried last and checked.
# Override with QML=/path/to/qml.
find_qml() {
    local cands=() c r t dir
    for t in qmake6 qmake-qt6; do
        command -v "$t" >/dev/null 2>&1 && { dir="$("$t" -query QT_INSTALL_BINS 2>/dev/null || true)"; [ -n "$dir" ] && cands+=("$dir/qml"); }
    done
    if command -v qtpaths6 >/dev/null 2>&1; then dir="$(qtpaths6 --binaries-dir 2>/dev/null || true)"; [ -n "$dir" ] && cands+=("$dir/qml"); fi
    cands+=(/usr/lib64/qt6/bin/qml /usr/lib/qt6/bin/qml /usr/lib/x86_64-linux-gnu/qt6/bin/qml /usr/lib/aarch64-linux-gnu/qt6/bin/qml
            /usr/libexec/qt6/qml qml6 qml-qt6 qml)
    for c in "${cands[@]}"; do
        r="$(command -v "$c" 2>/dev/null || true)"
        [ -n "$r" ] && [ -x "$r" ] || continue
        [[ "$(readlink -f "$r")" == *qtchooser* ]] && continue
        QT_QPA_PLATFORM=offscreen timeout 10 "$r" --help 2>&1 | grep -q -- "--apptype" || continue
        echo "$r"; return 0
    done
    return 1
}
QML="${QML:-}"
[ -n "$QML" ] || QML="$(find_qml || true)"
halcyon_env="${XDG_CONFIG_HOME:-$HOME/.config}/plasma-workspace/env/halcyon.sh"
sc_pid=""
fail_reason=""

launch_app() {   # launch_app <breeze|halcyon> <seconds to wait> <command...>
    local pass="$1" wait_for="$2"; shift 2
    (
        if [ "$pass" = halcyon ]; then
            [ -r "$halcyon_env" ] && . "$halcyon_env"          # Halcyon's Qt Quick switch and style plugin paths
        else
            unset QML_IMPORT_PATH QML2_IMPORT_PATH               # stock qqc2-desktop-style: Breeze's own switch
        fi
        export QT_QUICK_CONTROLS_STYLE=org.kde.desktop
        exec "$@"
    ) >"$tmp/app.log" 2>&1 &
    sc_pid=$!
    sleep "$wait_for"
}
run_showcase() {   # run_showcase <scene> <breeze|halcyon>
    if [ -z "$QML" ]; then
        fail_reason="no working Qt 6 qml tool found (a plain qml is usually the Qt 4/5 wrapper). Install the Qt 6 declarative tools (Fedora: qt6-qtdeclarative-devel, Arch: qt6-declarative, Debian/Ubuntu: qml-qt6) or set QML=/path/to/qt6/bin/qml"; return 1
    fi
    launch_app "$2" 3.5 "$QML" -a widget "$root/tools/showcase.qml" -- "$1"   # popup opens at about 0.7s
    if ! kill -0 "$sc_pid" 2>/dev/null; then   # still running? if not, the showcase failed to start
        fail_reason="$QML exited right away: $(grep -v '^QStandardPaths' "$tmp/app.log" | tail -n 4 | tr '\n' ' ')"; return 1
    fi
}
run_settings() {   # run_settings <breeze|halcyon>
    command -v systemsettings >/dev/null || { fail_reason="systemsettings not found"; return 1; }
    # If System Settings is already open it just raises that window and exits; we then close nothing of yours.
    launch_app "$1" 6 systemsettings ${SETTINGS_PAGE:+"$SETTINGS_PAGE"}   # no page = the start page (Quick Settings)
}
stop_showcase() { [ -n "$sc_pid" ] && kill "$sc_pid" 2>/dev/null || true; [ -n "$sc_pid" ] && wait "$sc_pid" 2>/dev/null || true; sc_pid=""; sleep 0.5; }

bg_pid=""
before_shot() {   # before_shot <scene> <breeze|halcyon>; returns 1 if the scene could not be set up
    case "$1" in
        desktop) ;;
        settings) run_settings "$2" || return 1 ;;
        controls|menu|combo) run_showcase "$1" "$2" || return 1 ;;
        volume)   # keep the overlay alive while the shot is taken
            dbus_call /org/kde/osdService org.kde.osdService.volumeChanged 60 || return 1
            ( for _ in 1 2 3 4 5 6 7 8; do sleep 0.4; dbus_call /org/kde/osdService org.kde.osdService.volumeChanged 60 || true; done ) &
            bg_pid=$!; sleep 0.7 ;;
        launcher) dbus_call /PlasmaShell org.kde.PlasmaShell.activateLauncherMenu || return 1; sleep 1.3 ;;
        notification)
            command -v notify-send >/dev/null || { fail_reason="notify-send not found"; return 1; }
            notify-send -t 3000 -a Halcyon -i dialog-information "Halcyon" "This is how a notification looks." || return 1
            sleep 1.5 ;;
        *)  # manual scene
            if [ "$count" -gt 0 ]; then notify "scene '$1': set it up now, capturing in ${count}s" 3500; sleep "$count"; fi ;;
    esac
}
after_shot() {
    case "$1" in
        settings|controls|menu|combo) stop_showcase ;;
        volume)   [ -n "$bg_pid" ] && wait "$bg_pid" 2>/dev/null || true; bg_pid=""; sleep 1 ;;
        launcher) dbus_call /PlasmaShell org.kde.PlasmaShell.activateLauncherMenu || true; sleep 0.8 ;;
        notification) sleep 2.5 ;;
    esac
}

declare -A bad=() boxes=()
crop_scene() { case "$1" in controls|menu|combo|volume|launcher|notification) return 0 ;; *) return 1 ;; esac; }   # settings and desktop stay full screen

# Bounding box (WxH+X+Y) of what changed between a "before" and an "after" shot: the window or popup and its shadow.
# Small specks (a ticking clock) are ignored. Prints nothing if nothing sizeable appeared.
changed_box() {   # changed_box <before.png> <after.png>
    local box w h
    box="$("${IM[@]}" "$1" "$2" -compose difference -composite -colorspace Gray -threshold 4% \
        -morphology Open Square:8 -format '%@' info: 2>/dev/null || true)"
    [[ "$box" =~ ^([0-9]+)x([0-9]+)\+([0-9]+)\+([0-9]+)$ ]] || return 0
    w="${BASH_REMATCH[1]}"; h="${BASH_REMATCH[2]}"
    [ $((w * h)) -ge 4000 ] && echo "$box"
    return 0
}

union_box() {   # union_box <box1> <box2> <image width> <image height>  ->  padded box that holds both
    local pad="${PAD:-28}" x0 y0 x1 y1 a b
    [[ "$1" =~ ^([0-9]+)x([0-9]+)\+([0-9]+)\+([0-9]+)$ ]] && a=("${BASH_REMATCH[@]}")
    [[ "$2" =~ ^([0-9]+)x([0-9]+)\+([0-9]+)\+([0-9]+)$ ]] && b=("${BASH_REMATCH[@]}")
    x0=$(( a[3] < b[3] ? a[3] : b[3] )); y0=$(( a[4] < b[4] ? a[4] : b[4] ))
    x1=$(( a[3] + a[1] > b[3] + b[1] ? a[3] + a[1] : b[3] + b[1] ))
    y1=$(( a[4] + a[2] > b[4] + b[2] ? a[4] + a[2] : b[4] + b[2] ))
    x0=$(( x0 - pad < 0 ? 0 : x0 - pad )); y0=$(( y0 - pad < 0 ? 0 : y0 - pad ))
    x1=$(( x1 + pad > $3 ? $3 : x1 + pad )); y1=$(( y1 + pad > $4 ? $4 : y1 + pad ))
    echo "$((x1 - x0))x$((y1 - y0))+$x0+$y0"
}

capture_pass() {   # capture_pass <prefix> <look-and-feel id> <label>
    plasma-apply-lookandfeel -a "$2" >/dev/null 2>&1
    sleep "$wait_s"
    local i n c f base box
    for i in "${!names[@]}"; do
        n="${names[$i]}"; c="${crops[$i]}"; f="$tmp/$1-$n.png"; base="$tmp/$1-$n-base.png"
        [ -n "${bad[$n]:-}" ] && continue
        [ "$n" = titlebar ] && continue   # cut from the controls shots later
        # an empty-desktop shot first, so the window can be found by what changes
        if crop_scene "$n" && [ -z "$c" ]; then spectacle -b -n -f -o "$base"; fi
        if ! before_shot "$n" "$1"; then
            bad[$n]=1; echo "skipping '$n': ${fail_reason:-could not set it up (the Plasma D-Bus call failed)}" >&2; fail_reason=""; continue
        fi
        spectacle -b -n -f -o "$f"
        after_shot "$n"
        [ -s "$f" ] || { echo "spectacle did not write $f (on Wayland, allow screenshots when asked)" >&2; exit 1; }
        if crop_scene "$n" && [ -z "$c" ]; then
            box="$(changed_box "$base" "$f")"
            if [ -z "$box" ]; then bad[$n]=1; echo "skipping '$n': nothing new appeared on screen" >&2; continue; fi
            boxes["$1:$n"]="$box"
        fi
    done
}

BG='#1c1c1e'
label() {   # label <png> <text> <outfile>
    "${IM[@]}" "$1" -background "$BG" -gravity south -splice 0x56 \
        -fill '#f2f2f7' -pointsize 28 -annotate +0+12 "$2" "$3"
}
# One image per scene, always Breeze on the left and Halcyon on the right, both cropped to the same area.
compose() {   # compose <scene>
    local n="$1" a="$tmp/breeze-$1.png" b="$tmp/halcyon-$1.png" c="" i W H h
    if [ ! -s "$a" ] || [ ! -s "$b" ]; then echo "skipping '$n': need both a Breeze and a Halcyon shot" >&2; return 1; fi
    cp "$a" "$tmp/full-breeze-$n.png"; cp "$b" "$tmp/full-halcyon-$n.png"
    for i in "${!names[@]}"; do [ "${names[$i]}" = "$n" ] && c="${crops[$i]}"; done
    if [ -z "$c" ] && [ -n "${boxes[breeze:$n]:-}" ] && [ -n "${boxes[halcyon:$n]:-}" ]; then
        read -r W H < <("${IDENT[@]}" -format '%w %h\n' "$a")
        c="$(union_box "${boxes[breeze:$n]}" "${boxes[halcyon:$n]}" "$W" "$H")"
    fi
    if [ -n "$c" ]; then
        "${IM[@]}" "$a" -crop "$c" +repage "$a"
        "${IM[@]}" "$b" -crop "$c" +repage "$b"
    fi
    if [ -n "${KEEP_RAW:-}" ]; then mkdir -p "$out/raw"; cp "$a" "$out/raw/breeze-$variant-$n.png"; cp "$b" "$out/raw/halcyon-$variant-$n.png"; fi
    label "$a" "$breeze_label"  "$tmp/a.png"
    label "$b" "$halcyon_label" "$tmp/b.png"
    h=$("${IDENT[@]}" -format '%h\n' "$tmp/a.png" "$tmp/b.png" | sort -n | tail -1)
    "${IM[@]}" "$tmp/a.png" -background "$BG" -gravity north -extent "x$h" "$tmp/a2.png"
    "${IM[@]}" "$tmp/b.png" -background "$BG" -gravity north -extent "x$h" "$tmp/b2.png"
    "${IM[@]}" "$tmp/a2.png" '(' -size "6x$h" "xc:$BG" ')' "$tmp/b2.png" +append "$out/compare-$variant-$n.png"
    echo "wrote $out/compare-$variant-$n.png"
}

# Close-up of the window buttons: the top strip of the controls window, Breeze above and Halcyon below.
compose_titlebar() {
    local src=controls fa="$tmp/full-breeze-controls.png" fb="$tmp/full-halcyon-controls.png" c W H w h x y strip="${TITLEBAR_H:-120}"
    if [ ! -s "$fa" ] || [ ! -s "$fb" ] || [ -z "${boxes[breeze:$src]:-}" ] || [ -z "${boxes[halcyon:$src]:-}" ]; then
        echo "skipping 'titlebar': it is cut from the 'controls' shots, which are missing" >&2; return 1
    fi
    read -r W H < <("${IDENT[@]}" -format '%w %h\n' "$fa")
    c="$(PAD=12 union_box "${boxes[breeze:$src]}" "${boxes[halcyon:$src]}" "$W" "$H")"
    [[ "$c" =~ ^([0-9]+)x([0-9]+)\+([0-9]+)\+([0-9]+)$ ]] || return 1
    w="${BASH_REMATCH[1]}"; h="${BASH_REMATCH[2]}"; x="${BASH_REMATCH[3]}"; y="${BASH_REMATCH[4]}"
    [ "$strip" -gt "$h" ] && strip="$h"
    "${IM[@]}" "$fa" -crop "${w}x${strip}+${x}+${y}" +repage "$tmp/ta0.png"
    "${IM[@]}" "$fb" -crop "${w}x${strip}+${x}+${y}" +repage "$tmp/tb0.png"
    if [ -n "${KEEP_RAW:-}" ]; then mkdir -p "$out/raw"; cp "$tmp/ta0.png" "$out/raw/breeze-$variant-titlebar.png"; cp "$tmp/tb0.png" "$out/raw/halcyon-$variant-titlebar.png"; fi
    label "$tmp/ta0.png" "$breeze_label"  "$tmp/ta.png"
    label "$tmp/tb0.png" "$halcyon_label" "$tmp/tb.png"
    "${IM[@]}" "$tmp/ta.png" '(' -size "${w}x6" "xc:$BG" ')' "$tmp/tb.png" -background "$BG" -append "$out/compare-$variant-titlebar.png"
    echo "wrote $out/compare-$variant-titlebar.png"
}

start_ms=$((start_s * 1000 - 500)); [ "$start_ms" -lt 1000 ] && start_ms=1000
notify "Starting in ${start_s}s. Scenes: ${names[*]}. Please don't touch the mouse or keyboard until it says done." "$start_ms"
sleep "$start_s"
capture_pass breeze  "$breeze_id"  "$breeze_label"
capture_pass halcyon "$halcyon_id" "$halcyon_label"
made=0
for n in "${names[@]}"; do
    [ "$n" = titlebar ] && continue
    [ -n "${bad[$n]:-}" ] && continue
    compose "$n" && made=$((made + 1))
done
for n in "${names[@]}"; do
    if [ "$n" = titlebar ]; then compose_titlebar && made=$((made + 1)); fi
done
notify "Done: $made comparison image(s) in $out" 10000
