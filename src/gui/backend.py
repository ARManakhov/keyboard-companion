from PyQt6.QtCore import QObject, QThreadPool, pyqtProperty, pyqtSignal, pyqtSlot
from typing import List, Optional
from core.device import DeviceInfo, get_devices
from gui.log import LogModel
from gui.scanner import DeviceScanner
from gui.device_thread import DeviceThread
from datetime import datetime


class Backend(QObject):
    devicesUpdated = pyqtSignal(list)
    scanningChanged = pyqtSignal(bool)
    connectedChanged = pyqtSignal(bool)
    deviceCapabilitiesChanged = pyqtSignal(list)
    keyboardLayoutChanged = pyqtSignal(str)
    mediaArtistChanged = pyqtSignal(str)
    mediaNameChanged = pyqtSignal(str)
    mediaCoverChanged = pyqtSignal(str)
    playbackStatusChanged = pyqtSignal(bool)
    playbackProgressChanged = pyqtSignal(int)
    clockChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._dev_info: List[DeviceInfo] = []
        self._selected_dev_info: Optional[DeviceInfo] = None
        self._pool = QThreadPool.globalInstance()
        self._device_thread: Optional[DeviceThread] = None
        self._device_connected = False
        self._device_capabilities: list = []

        self._keyboard_layout = ""
        self._media_artist = ""
        self._media_name = ""
        self._media_cover = ""
        self._playback_status = False
        self._playback_progress = 0
        self._log_model = LogModel()

    @pyqtProperty(bool, notify=connectedChanged)
    def deviceConnected(self):
        return self._device_connected

    @pyqtProperty(list, notify=deviceCapabilitiesChanged)
    def deviceCapabilities(self):
        return self._device_capabilities

    @pyqtProperty(str, notify=keyboardLayoutChanged)
    def keyboardLayout(self):
        return self._keyboard_layout

    @pyqtProperty(str, notify=mediaArtistChanged)
    def mediaArtist(self):
        return self._media_artist

    @pyqtProperty(str, notify=mediaNameChanged)
    def mediaName(self):
        return self._media_name

    @pyqtProperty(str, notify=mediaCoverChanged)
    def mediaCover(self):
        return self._media_cover

    @pyqtProperty(str, notify=playbackStatusChanged)
    def playbackStatus(self):
        if self._playback_status:
            return "Paused"
        return "Playing"

    @pyqtProperty(int, notify=playbackProgressChanged)
    def playbackProgress(self):
        return int(self._playback_progress / 255 * 100)

    @pyqtProperty(str, notify=clockChanged)
    def clock(self):
        return datetime.now().strftime("%Y %m %d %H:%M")

    @pyqtProperty(QObject, constant=True)
    def logModel(self):
        return self._log_model

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

        self._device_thread.connectedUpdated.connect(self._on_connected_updated)
        self._device_thread.capabilitiesUpdated.connect(self._on_capabilities_updated)

        self._device_thread.keyboardLayoutUpdated.connect(self._on_keyboard_layout)
        self._device_thread.mediaArtistUpdated.connect(self._on_media_artist)
        self._device_thread.mediaNameUpdated.connect(self._on_media_name)
        self._device_thread.mediaCoverUpdated.connect(self._on_media_cover)
        self._device_thread.playbackStatusUpdated.connect(self._on_playback_status)
        self._device_thread.playbackProgressUpdated.connect(self._on_playback_progress)

        self._device_thread.clockUpdated.connect(self._on_clock)

        self._device_thread.start()

    def _on_connected_updated(self, connected: bool):
        self._set_connected(connected)

    def _on_capabilities_updated(self, caps: list):
        self._device_capabilities = caps
        self.deviceCapabilitiesChanged.emit(caps)

    def _on_keyboard_layout(self, data: str):
        self._keyboard_layout = data
        self.keyboardLayoutChanged.emit(data)

    def _on_media_artist(self, data):
        self._media_artist = data
        self.mediaArtistChanged.emit(data)

    def _on_media_name(self, data):
        self._media_name = data
        self.mediaNameChanged.emit(data)

    def _on_media_cover(self, data):
        self._media_cover = data
        self.mediaCoverChanged.emit(data)

    def _on_playback_status(self, data: bool):
        self._playback_status = data
        self.playbackStatusChanged.emit(data)

    def _on_playback_progress(self, data: int):
        self._playback_progress = data
        self.playbackProgressChanged.emit(data)

    def _on_clock(self):
        self.clockChanged.emit()

    @pyqtSlot()
    def disconnect(self):
        if self._device_thread is not None:
            self._device_thread.stop()
            self._device_thread = None
        self._set_connected(False)

    def _on_device_error(self, msg: str):
        print(f"Device error: {msg}")
        self._set_connected(False)
