import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "tabs"

ApplicationWindow {
    id: window
    title: "Keyboard companion"

    Connections {
        target: backend
        function onDevicesUpdated(devices) {
            deviceSelector.model = devices;
        }
        function onScanningChanged(scanning) {
            deviceSelector.scanning = scanning;
        }
    }

    Column {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        DeviceSelector {
            id: deviceSelector
            width: parent.width
            scanning: false
            onRefreshRequested: backend.refresh_devices()
            onDeviceSelected: (index) => backend.connect_to(index)
            Component.onCompleted: backend.refresh_devices()
        }

        TabBar {
            id: bar
            width: parent.width
            TabButton { text: "Status"; implicitHeight: 28 }
            TabButton { text: "Logs"; implicitHeight: 28 }
            TabButton { text: "Info"; implicitHeight: 28 }
        }

        StackLayout {
            width: parent.width
            height: parent.height - bar.height - deviceSelector.height - 20
            currentIndex: bar.currentIndex

            StatusTab {}
            LogsTab {}
            InfoTab {}
        }
    }
}
