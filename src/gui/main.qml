import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 600
    height: 300
    title: "Keyboard companion"

    Connections {
        target: backend
        function onDevicesUpdated(devices) {
            deviceComboBox.model = devices;
        }
        function onScanningChanged(scanning) {
            btnRefresh.text = scanning ? "Scanning..." : "Refresh";
            btnRefresh.enabled = !scanning;
        }
    }

    Row {
        id: topRow
        spacing: 6
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10

        ComboBox {
            id: deviceComboBox
            width: parent.width - btnRefresh.width - parent.spacing
            model: []

            Component.onCompleted: {
                backend.refresh_devices();
            }

            onCurrentIndexChanged: {
                if (currentIndex >= 0) {
                    backend.connect_to(currentIndex);
                }
            }
        }

        Button {
            id: btnRefresh
            text: "Refresh"
            width: implicitWidth
            onClicked: {
                backend.refresh_devices();
            }
        }
    }

    Column {
        id: tabContainer
        spacing: 0
        anchors.top: topRow.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: 10
        anchors.bottomMargin: 10
        anchors.leftMargin: 10
        anchors.rightMargin: 10

        TabBar {
            id: bar
            width: parent.width
            z: 1

            TabButton {
                text: "Status"
                implicitHeight: 28
            }
            TabButton {
                text: "Logs"
                implicitHeight: 28
            }
            TabButton {
                text: "Info"
                implicitHeight: 28
            }
        }

        Frame {
            width: parent.width
            height: parent.height - bar.height
            padding: 10
            background: Rectangle {
                color: palette.window
            }

            Item {
                anchors.fill: parent
                visible: bar.currentIndex === 0

                Row {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        width: parent.width / 2
                        height: parent.height
                        color: palette.window

                        Column {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10

                            Row {
                                spacing: 8
                                Text {
                                    color: palette.windowText
                                    text: "Status:"
                                    font.bold: true
                                }
                                Text {
                                    color: palette.windowText
                                    text: backend.deviceConnected ? "Connected" : "Disconnected"
                                    font.bold: true
                                }
                            }

                            Rectangle {
                                width: parent.width
                                height: 1
                                color: palette.mid
                            }

                            Text {
                                color: palette.windowText
                                text: "Capabilities:"
                                font.bold: true
                            }

                            ListView {
                                width: parent.width
                                height: parent.height - y
                                spacing: 4
                                model: backend.deviceCapabilities
                                clip: true

                                delegate: Text {
                                    color: palette.windowText
                                    text: "• " + modelData
                                }
                            }
                        }
                    }

                    Rectangle {
                        width: 1
                        height: parent.height
                        color: palette.mid
                    }

                    Rectangle {
                        width: parent.width / 2 - 1
                        height: parent.height
                        color: palette.window
                    }
                }
            }

            Item {
                anchors.fill: parent
                visible: bar.currentIndex === 1
                Text {
                    color: palette.windowText
                    text: "Placeholder for logs"
                }
            }

            Item {
                anchors.fill: parent
                visible: bar.currentIndex === 2
                Text {
                    color: palette.windowText
                    text: "Placeholder for info"
                }
            }
        }
    }
}
