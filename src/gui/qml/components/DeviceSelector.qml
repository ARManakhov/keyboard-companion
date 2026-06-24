import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Row {
    spacing: 6
    property alias model: comboBox.model
    property alias currentIndex: comboBox.currentIndex
    property bool scanning: false

    signal refreshRequested()
    signal deviceSelected(int index)

    ComboBox {
        id: comboBox
        width: parent.width - btnRefresh.width - parent.spacing
        model: []
        onCurrentIndexChanged: if (currentIndex >= 0) parent.deviceSelected(currentIndex)
    }

    Button {
        id: btnRefresh
        text: parent.scanning ? "Scanning..." : "Refresh"
        enabled: !parent.scanning
        onClicked: parent.refreshRequested()
    }
}
