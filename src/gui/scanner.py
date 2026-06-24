from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

class WorkerSignals(QObject):
    devices_found = pyqtSignal(list)
    error = pyqtSignal(str)
    finished = pyqtSignal()

class DeviceScanner(QRunnable):
    def __init__(self, scan_fn):
        super().__init__()
        self.scan_fn = scan_fn
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.scan_fn()
            self.signals.devices_found.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()
