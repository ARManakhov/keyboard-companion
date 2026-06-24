import sys
from pathlib import Path
from PyQt6.QtQml import (
    QQmlApplicationEngine,
)
from PyQt6.QtCore import QUrl
from gui.backend import Backend
from PyQt6.QtWidgets import QApplication

from gui.log import StdoutCapture
from gui.tray import TrayController


def init():
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    capture = StdoutCapture(sys.stdout, backend.logModel)
    sys.stdout = capture
    sys.stderr = capture
    engine.rootContext().setContextProperty("stdoutCapture", capture)

    base_dir = Path(__file__).resolve().parent
    qml_path = base_dir / "qml" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))

    if not engine.rootObjects():
        sys.exit(-1)

    root_window = engine.rootObjects()[0]

    tray = TrayController(app, root_window)
    root_window.installEventFilter(tray)

    app.aboutToQuit.connect(tray.tray.hide)

    sys.exit(app.exec())
