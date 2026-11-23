// A window full of ordinary controls, used by tools/compare_screenshots.sh so Breeze and Halcyon are shown with
// the same content. Run through the `qml` tool with the widget application type so it uses your widget style:
//
//   QT_QUICK_CONTROLS_STYLE=org.kde.desktop qml -a widget tools/showcase.qml -- [controls|menu|combo]
//
//   controls  the plain window (default)
//   menu      the same window with a menu open
//   combo     the same window with a drop-down list open
//
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: win

    readonly property var args: Qt.application.arguments
    readonly property string scene: args.indexOf("menu") >= 0 ? "menu" : (args.indexOf("combo") >= 0 ? "combo" : "controls")

    visible: true
    title: "Halcyon showcase"
    width: Math.round(Math.min(1040, Screen.desktopAvailableWidth * 0.62))
    height: Math.round(Math.min(680, Screen.desktopAvailableHeight * 0.72))
    minimumWidth: 860
    minimumHeight: 560

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 8
            anchors.rightMargin: 8
            ToolButton {
                id: menuButton
                text: "Menu"
                onClicked: menu.open()
                Menu {
                    id: menu
                    y: menuButton.height
                    MenuItem { text: "New window" }
                    MenuItem { text: "Open..." }
                    MenuItem { text: "Show hidden files"; checkable: true; checked: true }
                    MenuSeparator {}
                    Menu {
                        title: "Sort by"
                        MenuItem { text: "Name"; checkable: true; checked: true }
                        MenuItem { text: "Size"; checkable: true }
                        MenuItem { text: "Date"; checkable: true }
                    }
                    MenuItem { text: "Disabled item"; enabled: false }
                    MenuSeparator {}
                    MenuItem { text: "Quit" }
                }
            }
            ToolButton { text: "Back" }
            ToolButton { text: "Forward"; enabled: false }
            Item { Layout.fillWidth: true }
            TextField { placeholderText: "Search"; Layout.preferredWidth: 220 }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        TabBar {
            id: tabs
            Layout.fillWidth: true
            TabButton { text: "Controls" }
            TabButton { text: "Lists" }
            TabButton { text: "Text" }
        }

        GridLayout {
            columns: 2
            columnSpacing: 20
            rowSpacing: 16
            Layout.fillWidth: true
            Layout.fillHeight: true

            GroupBox {
                title: "Buttons"
                Layout.fillWidth: true
                RowLayout {
                    spacing: 10
                    Button { text: "Default" }
                    Button { text: "Highlighted"; highlighted: true }
                    Button { text: "Flat"; flat: true }
                    Button { text: "Disabled"; enabled: false }
                }
            }

            GroupBox {
                title: "Switches"
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 6
                    Switch { text: "Wi-Fi"; checked: true }
                    Switch { text: "Bluetooth" }
                    Switch { text: "Do not disturb"; checked: true; enabled: false }
                }
            }

            GroupBox {
                title: "Choices"
                Layout.fillWidth: true
                RowLayout {
                    spacing: 28
                    ColumnLayout {
                        CheckBox { text: "Checked"; checked: true }
                        CheckBox { text: "Unchecked" }
                        CheckBox { text: "Partly"; checkState: Qt.PartiallyChecked; tristate: true }
                    }
                    ColumnLayout {
                        RadioButton { text: "First"; checked: true }
                        RadioButton { text: "Second" }
                        RadioButton { text: "Third" }
                    }
                }
            }

            GroupBox {
                title: "Values"
                Layout.fillWidth: true
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    spacing: 10
                    Slider { Layout.fillWidth: true; value: 0.6 }
                    ProgressBar { Layout.fillWidth: true; value: 0.4 }
                    RowLayout {
                        spacing: 10
                        SpinBox { value: 42 }
                        ComboBox {
                            id: combo
                            Layout.fillWidth: true
                            model: ["Halcyon Night", "Halcyon Day", "Breeze", "Breeze Dark", "Oxygen"]
                        }
                    }
                }
            }

            GroupBox {
                title: "List"
                Layout.fillWidth: true
                Layout.columnSpan: 2
                Layout.fillHeight: true
                ListView {
                    anchors.fill: parent
                    clip: true
                    model: ["Documents", "Downloads", "Music", "Pictures", "Videos"]
                    delegate: ItemDelegate {
                        width: ListView.view.width
                        text: modelData
                        highlighted: index === 1
                    }
                    ScrollBar.vertical: ScrollBar {}
                }
            }
        }
    }

    // Open the requested popup once the window is up.
    Timer {
        interval: 700
        running: true
        onTriggered: {
            if (win.scene === "menu")
                menu.open()
            else if (win.scene === "combo")
                combo.popup.open()
        }
    }
}
