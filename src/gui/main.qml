import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: window
    visible: true
    width: 600
    height: 300
    title: "Keyboard companion"

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
                deviceComboBox.model = backend.list_devs();
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
                deviceComboBox.model = backend.list_devs();
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

            Item {
                anchors.fill: parent
                visible: bar.currentIndex === 0
                Text {
                    color: window.palette.windowText
                    text: "Placeholder for status"
                }
            }

            Item {
                anchors.fill: parent
                visible: bar.currentIndex === 1
                Text {
                    color: window.palette.windowText
                    text: "Placeholder for logs"
                }
            }

            Item {
                anchors.fill: parent
                visible: bar.currentIndex === 2
                Text {
                    color: window.palette.windowText
                    text: "Placeholder for info"
                }
            }
        }
    }
}
