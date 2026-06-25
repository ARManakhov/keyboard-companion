from pathlib import Path
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QObject, pyqtSlot, QEvent


class TrayController(QObject):
    def __init__(self, app, window, icon):
        super().__init__()
        self._app = app
        self._window = window

        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this system")
            return

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(icon)

        self.tray.setToolTip("Keyboard Companion")

        self.menu = QMenu()
        self._show_action = QAction("Show", self)
        self._hide_action = QAction("Hide", self)
        self._quit_action = QAction("Quit", self)

        self._show_action.triggered.connect(self.show_window)
        self._quit_action.triggered.connect(self.quit)

        self.menu.addAction(self._show_action)
        self.menu.addSeparator()
        self.menu.addAction(self._quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)

        self._app.setQuitOnLastWindowClosed(False)

        self.tray.show()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window()

    @pyqtSlot()
    def show_window(self):
        self._window.show()
        self._window.raise_()
        self._window.requestActivate()

    @pyqtSlot()
    def hide_window(self):
        self._window.hide()

    @pyqtSlot()
    def toggle_window(self):
        if self._window.isVisible():
            self.hide_window()
        else:
            self.show_window()

    @pyqtSlot()
    def quit(self):
        self.tray.hide()
        self._app.quit()

    def eventFilter(self, watched, event):
        if watched is self._window and event.type() == QEvent.Type.Close:
            self.hide_window()
            return True
        return super().eventFilter(watched, event)
