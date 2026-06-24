from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional
from core.device import Device, DeviceInfo
from core.clock import AlignedTimer
from core.monitor import get_monitor_class

INTERVAL_SEC = 15.0

class DeviceThread(QThread):
    error = pyqtSignal(str)
    capabilitiesUpdated = pyqtSignal(list)
    connectedUpdated = pyqtSignal(bool)

    def __init__(self, dev_info: DeviceInfo):
        super().__init__()
        self._dev_info = dev_info
        self._device: Optional[Device] = None
        self._timer: Optional[AlignedTimer] = None
        self._monitor = None
        self._stopped = False

    def run(self):
        try:
            self._device = Device(
                self._dev_info.vid,
                self._dev_info.pid,
                self._dev_info.interface,
                reconnect_callback=[self._on_reconnected],
                disconnect_callback=[self._on_disconnected],
                capabilitis_callback=[self._on_capabilities],
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

            while not self._stopped:
                self.msleep(100)

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self._cleanup()

    def _cleanup(self):
        if self._timer:
            self._timer.stop()
        if self._device:
            self._device.close()

    def _on_reconnected(self):
        self.connectedUpdated.emit(True)

    def _on_disconnected(self):
        self.connectedUpdated.emit(False)

    def _on_capabilities(self, capabilities: list):
        self.capabilitiesUpdated.emit(capabilities)

    def stop(self):
        self._stopped = True
        if self._device:
            for cb in [self._on_reconnected, self._on_disconnected, self._on_capabilities]:
                try:
                    self._device.reconnect_callback.remove(cb)
                except ValueError:
                    pass
            self._device.close()
        if self._timer:
            self._timer.stop()
        self.wait(2000)
