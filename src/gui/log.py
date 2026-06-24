from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSlot, QObject

from PyQt6.QtCore import pyqtSignal


class LogModel(QAbstractListModel):
    LineRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lines = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._lines)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._lines):
            return None
        if role in (Qt.ItemDataRole.DisplayRole, self.LineRole):
            return self._lines[index.row()]
        return None

    def roleNames(self):
        return {self.LineRole: b"line"}

    @pyqtSlot(str)
    def append(self, text: str):
        self.beginInsertRows(QModelIndex(), len(self._lines), len(self._lines))
        self._lines.append(text)
        self.endInsertRows()

    @pyqtSlot()
    def clear(self):
        self.beginResetModel()
        self._lines.clear()
        self.endResetModel()


class StdoutCapture(QObject):
    newLine = pyqtSignal(str)

    def __init__(self, original, log_model=None):
        super().__init__()
        self._original = original
        self._log_model = log_model

    def write(self, text: str):
        stripped = text.rstrip("\n")
        if stripped:
            self.newLine.emit(stripped)
            if self._log_model:
                self._log_model.append(stripped)
        self._original.write(text)
        self._original.flush()

    def flush(self):
        self._original.flush()
