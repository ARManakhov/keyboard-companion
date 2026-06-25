import QtQuick
import QtQuick.Controls

Item {
    Column {
        anchors.centerIn: parent
        spacing: 8

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            color: palette.windowText
            text: "Keyboard Companion is app to send various data to QMK keyboard"
        }

        Text {
            id: linkText
            anchors.horizontalCenter: parent.horizontalCenter
            color: palette.windowText
            textFormat: Text.RichText
            text: "source code can be found <a href=\"https://github.com/ARManakhov/keyboard-companion\">here</a>"

            onLinkActivated: link => {
                Qt.openUrlExternally(link);
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
                cursorShape: linkText.hoveredLink ? Qt.PointingHandCursor : Qt.ArrowCursor
            }
        }
    }
}
