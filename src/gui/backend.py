from PyQt6.QtCore import QObject, QThreadPool, pyqtProperty, pyqtSignal, pyqtSlot
from typing import List, Optional
from core.device import DeviceInfo, get_devices
from gui.scanner import DeviceScanner
from gui.device_thread import DeviceThread


class Backend(QObject):
    devicesUpdated = pyqtSignal(list)
    scanningChanged = pyqtSignal(bool)
    connectedChanged = pyqtSignal(bool)
    deviceCapabilitiesChanged = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._dev_info: List[DeviceInfo] = []
        self._selected_dev_info: Optional[DeviceInfo] = None
        self._pool = QThreadPool.globalInstance()
        self._device_thread: Optional[DeviceThread] = None
        self._device_connected = False
        self._device_capabilities: list = []

    @pyqtProperty(bool, notify=connectedChanged)
    def deviceConnected(self):
        return self._device_connected

    @pyqtProperty(list, notify=deviceCapabilitiesChanged)
    def deviceCapabilities(self):
        return self._device_capabilities

    def _set_connected(self, connected: bool):
        if self._device_connected != connected:
            self._device_connected = connected
            self.connectedChanged.emit(connected)
            if not connected:
                self._device_capabilities = []
                self.deviceCapabilitiesChanged.emit([])

    @pyqtSlot()
    def refresh_devices(self):
        self.scanningChanged.emit(True)
        worker = DeviceScanner(get_devices)
        worker.signals.devices_found.connect(self._on_devices_found)
        worker.signals.error.connect(self._on_scan_error)
        worker.signals.finished.connect(lambda: self.scanningChanged.emit(False))
        self._pool.start(worker)

    def _on_devices_found(self, devices: list):
        self._dev_info = devices
        self.devicesUpdated.emit(devices)

    def _on_scan_error(self, msg: str):
        print(f"Scan error: {msg}")

    @pyqtSlot(int)
    def connect_to(self, dev_index: int):
        if self._device_thread is not None:
            self._device_thread.stop()
            self._device_thread = None
            self._set_connected(False)

        if not (0 <= dev_index < len(self._dev_info)):
            return

        self._selected_dev_info = self._dev_info[dev_index]
        self._device_thread = DeviceThread(self._selected_dev_info)
        self._device_thread.error.connect(self._on_device_error)
        self._device_thread.capabilitiesUpdated.connect(self._on_capabilities_updated)
        self._device_thread.connectedUpdated.connect(self._on_connected_updated)
        self._device_thread.start()

    def _on_connected_updated(self, connected: bool):
        self._set_connected(connected)

    def _on_capabilities_updated(self, caps: list):
        self._device_capabilities = caps
        self.deviceCapabilitiesChanged.emit(caps)

    @pyqtSlot()
    def disconnect(self):
        if self._device_thread is not None:
            self._device_thread.stop()
            self._device_thread = None
        self._set_connected(False)

    def _on_device_error(self, msg: str):
        print(f"Device error: {msg}")
        self._set_connected(False)
