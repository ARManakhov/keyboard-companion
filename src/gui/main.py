import sys
from pathlib import Path
from typing import List, Optional
from PyQt6.QtCore import QUrl
from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from device import Device, DeviceInfo, get_devices


class Backend(QObject):
    def __init__(self):
        self.dev_info: List[DeviceInfo] = []
        self.selected_dev_info: Optional[DeviceInfo] = None
        super().__init__()

    @pyqtSlot(result=list)
    def list_devs(self):
        self.dev_info = get_devices()
        return self.dev_info

    @pyqtSlot(int)
    def connect_to(self, dev_index):
        if 0 <= dev_index < len(self.dev_info):
            self.selected_dev_info = self.dev_info[dev_index]


def init():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    backend = Backend()

    context = engine.rootContext()
    context.setContextProperty("backend", backend)
    BASE_DIR = Path(__file__).resolve().parent

    qml_path = qml_path = BASE_DIR / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
