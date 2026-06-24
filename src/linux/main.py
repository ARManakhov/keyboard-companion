from .media import MediaPlayerMonitor
from .keyboard import KeyboardLayoutMonitor
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


class Monitor:
    def __init__(
        self,
        layout_callback=[],
        info_callback=[],
        status_callback=[],
        progress_callback=[],
    ):
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.loop = GLib.MainLoop()

        self.keyboard = KeyboardLayoutMonitor(self.bus, callback=layout_callback)
        self.media = MediaPlayerMonitor(
            self.bus,
            info_callback=info_callback,
            status_callback=status_callback,
            progress_callback=progress_callback,
        )

    def call_on_reconnect(self):
        return self.keyboard.call_on_reconnect() + self.media.call_on_reconnect()

    def start(self):
        self.media.start()
        self.keyboard.start()

        try:
            self.loop.run()
        except KeyboardInterrupt:
            self.loop.quit()
            self.media.stop()
