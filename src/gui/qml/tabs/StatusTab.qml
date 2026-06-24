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

            Column {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                Row {
                    spacing: 8
                    Text {
                        color: palette.windowText
                        text: "Layout:"
                        font.bold: true
                    }
                    Text {
                        color: palette.windowText
                        text: backend.keyboardLayout
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
                    text: "Media"
                    font.bold: true
                    font.pixelSize: 14
                }

                Row {
                    spacing: 8
                    Text {
                        color: palette.windowText
                        text: "Artist:"
                        font.bold: true
                    }
                    Text {
                        color: palette.windowText
                        text: backend.mediaArtist
                    }
                }

                Row {
                    spacing: 8
                    Text {
                        color: palette.windowText
                        text: "Track:"
                        font.bold: true
                    }
                    Text {
                        color: palette.windowText
                        text: backend.mediaName
                    }
                }

                Row {
                    spacing: 8
                    Text {
                        color: palette.windowText
                        text: "Status:"
                        font.bold: true
                    }
                    Text {
                        color: palette.windowText
                        text: backend.playbackStatus
                    }
                }

                Image {
                    width: 120
                    height: 120
                    fillMode: Image.PreserveAspectFit
                    source: backend.mediaCover
                    visible: backend.mediaCover !== ""
                }

                ProgressBar {
                    height: 10
                    width: parent.width
                    from: 0
                    to: 100
                    value: backend.playbackProgress
                }

                Rectangle {
                    width: parent.width
                    height: 1
                    color: palette.mid
                }

                Text {
                    color: palette.windowText
                    text: "Clock"
                    font.bold: true
                    font.pixelSize: 14
                }

                Row {
                    spacing: 8
                    Text {
                        color: palette.windowText
                        text: "Time and date:"
                        font.bold: true
                    }
                    Text {
                        color: palette.windowText
                        text: backend.clock
                    }
                }
            }
        }
    }
}
