import sys
from pathlib import Path
from PyQt6.QtQml import (
    QQmlApplicationEngine,
)
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QIcon
from gui.backend import Backend
from gui.log import StdoutCapture
from gui.tray import TrayController


def get_icon(base_dir):
    icon_path = base_dir.parent / "assets" / "icon.png"
    try:
        if icon_path and Path(icon_path).exists():
            return QIcon(str(icon_path))
    except Exception as e:
        print(f"can't load icon : {e}")

    return QIcon.fromTheme("input-keyboard")


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

    icon = get_icon(base_dir)

    app.setWindowIcon(icon)
    root_window = engine.rootObjects()[0]

    tray = TrayController(app, root_window, icon)
    root_window.installEventFilter(tray)

    app.aboutToQuit.connect(tray.tray.hide)

    sys.exit(app.exec())
