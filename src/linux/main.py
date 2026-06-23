from .media import MediaPlayerMonitor
from .keyboard import KeyboardLayoutMonitor
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


class Monitor:
    def __init__(self, device):
        self.device = device
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.loop = GLib.MainLoop()

        self.keyboard = KeyboardLayoutMonitor(device, self.bus)
        self.media = MediaPlayerMonitor(device, self.bus)

    def start(self):
        self.media.start()
        self.keyboard.start()

        try:
            self.loop.run()
        except KeyboardInterrupt:
            self.loop.quit()
            self.media.stop()
