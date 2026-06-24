import QtQuick
import QtQuick.Controls

Item {
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
                    Text { color: palette.windowText; text: "Status:"; font.bold: true }
                    Text {
                        color: palette.windowText
                        text: backend.deviceConnected ? "Connected" : "Disconnected"
                        font.bold: true
                    }
                }

                Rectangle { width: parent.width; height: 1; color: palette.mid }

                Text { color: palette.windowText; text: "Capabilities:"; font.bold: true }

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

        Rectangle { width: 1; height: parent.height; color: palette.mid }

        Rectangle {
            width: parent.width / 2 - 1
            height: parent.height
            color: palette.window
        }
    }
}
