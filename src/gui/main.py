import sys
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import (
    QObject,
    QRunnable,
    QThread,
    QThreadPool,
    QUrl,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from device import Device, DeviceInfo, get_devices
from clock import AlignedTimer
from uitls import get_monitor_class

INTERVAL_SEC = 30.0


class WorkerSignals(QObject):
    devices_found = pyqtSignal(list)
    error = pyqtSignal(str)
    finished = pyqtSignal()


class DeviceWorker(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn()
            self.signals.devices_found.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class DeviceThread(QThread):
    error = pyqtSignal(str)

    def __init__(self, dev_info: DeviceInfo):
        super().__init__()
        self._dev_info = dev_info
        self._device: Optional[Device] = None
        self._timer: Optional[AlignedTimer] = None
        self._monitor = None

    def run(self):
        try:
            self._device = Device(
                self._dev_info.vid,
                self._dev_info.pid,
                self._dev_info.interface,
                debug=False,
            )
            if not self._device:
                self.error.emit("Device not found")
                return

            self._timer = AlignedTimer(INTERVAL_SEC, self._device.send_time)
            self._timer.start(fire_immediately=True)

            Monitor = get_monitor_class()
            self._monitor = Monitor(self._device)

            self._monitor.start()

        except Exception as e:
            self.error.emit(str(e))
        finally:
            if self._timer:
                self._timer.stop()
            if self._device:
                self._device.close()

    def stop(self):
        if self._timer:
            self._timer.stop()
        if self._device:
            self._device.close()
        self.wait(2000)


class Backend(QObject):
    devicesUpdated = pyqtSignal(list)
    scanningChanged = pyqtSignal(bool)
    connectedChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.dev_info: List[DeviceInfo] = []
        self.selected_dev_info: Optional[DeviceInfo] = None
        self._pool = QThreadPool.globalInstance()
        self._device_thread: Optional[DeviceThread] = None

    @pyqtSlot()
    def refresh_devices(self):
        self.scanningChanged.emit(True)
        worker = DeviceWorker(get_devices)
        worker.signals.devices_found.connect(self._on_devices_found)
        worker.signals.error.connect(self._on_scan_error)
        worker.signals.finished.connect(lambda: self.scanningChanged.emit(False))
        self._pool.start(worker)

    def _on_devices_found(self, devices: list):
        self.dev_info = devices
        self.devicesUpdated.emit(devices)

    def _on_scan_error(self, msg: str):
        print(f"Scan error: {msg}")

    @pyqtSlot(int)
    def connect_to(self, dev_index: int):
        if self._device_thread is not None:
            self._device_thread.stop()
            self._device_thread = None
            self.connectedChanged.emit(False)

        if not (0 <= dev_index < len(self.dev_info)):
            return

        self.selected_dev_info = self.dev_info[dev_index]
        self._device_thread = DeviceThread(self.selected_dev_info)
        self._device_thread.error.connect(self._on_device_error)
        self._device_thread.finished.connect(self._on_device_finished)
        self._device_thread.start()
        self.connectedChanged.emit(True)

    @pyqtSlot()
    def disconnect(self):
        if self._device_thread is not None:
            self._device_thread.stop()
            self._device_thread = None
        self.connectedChanged.emit(False)

    def _on_device_error(self, msg: str):
        print(f"Device error: {msg}")
        self.connectedChanged.emit(False)

    def _on_device_finished(self):
        self._device_thread = None
        self.connectedChanged.emit(False)


def init():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    base_dir = Path(__file__).resolve().parent
    qml_path = base_dir / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))

    if not engine.rootObjects():
        sys.exit(-1)

    app.aboutToQuit.connect(backend.disconnect)

    sys.exit(app.exec())
