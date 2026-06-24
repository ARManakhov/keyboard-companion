import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    Layout.fillWidth: true
    Layout.fillHeight: true

    Column {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6

        Row {
            spacing: 8
            Button {
                text: "Clear"
                onClicked: backend.logModel.clear()
            }
            CheckBox {
                id: followTail
                text: "Auto-scroll"
                checked: true
            }
        }

        ListView {
            id: logView
            width: parent.width
            height: parent.height - y
            clip: true
            model: backend.logModel
            spacing: 2

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            delegate: Text {
                text: line
                font.family: "Monospace"
                font.pixelSize: 12
                color: palette.windowText
                wrapMode: Text.Wrap
                width: logView.width
            }

            onCountChanged: {
                if (followTail.checked) {
                    positionViewAtEnd();
                }
            }
        }
    }
}
