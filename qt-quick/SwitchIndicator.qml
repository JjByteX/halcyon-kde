/*
    Halcyon switch for qqc2-desktop-style (replaces org.kde.desktop/private/SwitchIndicator.qml).

    Flat pill track, white pill knob inset evenly on all four sides. Off = grey track, on = accent-coloured track (blue by
    default) with a slightly darker 1px edge. Same design and colours as the Plasma theme switch.svg (tools/gen_switch.py).
    Symmetric by construction: the knob travels between `ring` and width - ring - knobWidth.

    SPDX-License-Identifier: LGPL-3.0-only OR GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Templates as T
import org.kde.kirigami as Kirigami

Item {
    id: indicator

    property T.AbstractButton control
    property alias handle: handle

    implicitHeight: Math.round(Kirigami.Units.gridUnit * 1.25)
    implicitWidth: Math.round(implicitHeight * 2.2)
    opacity: control && !control.enabled ? 0.6 : 1
    layer.enabled: opacity < 1.0

    Kirigami.Theme.colorSet: Kirigami.Theme.Button
    Kirigami.Theme.inherit: false

    readonly property bool dark: Kirigami.Theme.backgroundColor.hslLightness < 0.5
    // Even gap between track and knob (about 1/16 of the height, never thinner than 1px).
    readonly property int ring: Math.max(1, Math.round(height / 16))
    readonly property real knobWidth: Math.round((width - 2 * ring) * 0.575)
    readonly property real stretch: control && control.down ? Math.round(height / 6) : 0

    readonly property color onFill: Kirigami.Theme.highlightColor
    readonly property color onEdge: Qt.darker(onFill, 1.2)
    readonly property real travelStart: ring
    readonly property real travelEnd: width - ring - knobWidth - stretch

    // Off track
    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: Qt.alpha(Kirigami.Theme.textColor, indicator.dark ? 0.15 : 0.10)
        border.width: 1
        border.color: indicator.dark ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(0, 0, 0, 0.045)
    }

    // On track: fades in with the knob's travel, so there is no geometry to get out of step and nothing to be lopsided
    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: indicator.onFill
        border.width: 1
        border.color: indicator.onEdge
        opacity: indicator.travelEnd > indicator.travelStart
            ? Math.max(0, Math.min(1, (handle.x - indicator.travelStart) / (indicator.travelEnd - indicator.travelStart)))
            : 0
    }

    Rectangle {
        id: handle

        x: indicator.control
            ? Math.max(indicator.travelStart, Math.min(indicator.travelEnd,
                  indicator.travelStart + indicator.control.visualPosition * (indicator.travelEnd - indicator.travelStart)))
            : indicator.travelStart
        y: indicator.ring
        width: indicator.knobWidth + indicator.stretch
        height: indicator.height - 2 * indicator.ring
        radius: height / 2
        color: indicator.control && indicator.control.down ? (indicator.dark ? "#e4e4e6" : "#f1f1f2") : "#ffffff"

        Behavior on x {
            enabled: indicator.control && !indicator.control.pressed && Kirigami.Units.shortDuration > 0
            SmoothedAnimation {
                duration: Kirigami.Units.shortDuration
            }
        }
        Behavior on width {
            enabled: Kirigami.Units.shortDuration > 0
            NumberAnimation {
                duration: Kirigami.Units.shortDuration
            }
        }
        Behavior on color {
            enabled: Kirigami.Units.shortDuration > 0
            ColorAnimation {
                duration: Kirigami.Units.shortDuration
            }
        }
    }

    // Keyboard focus: thin accent ring hugging the knob
    Rectangle {
        anchors.fill: handle
        anchors.margins: -indicator.ring
        radius: height / 2
        color: "transparent"
        border.width: indicator.ring
        border.color: Qt.alpha(Kirigami.Theme.highlightColor, 0.75)
        visible: indicator.control && indicator.control.visualFocus
    }
}
