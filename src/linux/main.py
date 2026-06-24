from .media import MediaPlayerMonitor
from .keyboard import KeyboardLayoutMonitor
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


class Monitor:
    def __init__(self, device, layout_callback=[]):
        self.device = device
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.loop = GLib.MainLoop()

        layout_callback.append(self.device.send_keyboard_layout)
        self.keyboard = KeyboardLayoutMonitor(self.bus, callback=layout_callback)
        self.media = MediaPlayerMonitor(
            self.bus,
            info_callback=[device.send_media_info],
            status_callback=[device.send_playback_status],
            progress_callback=[device.send_playback_progress],
        )
        device.reconnect_callback.extend(self.keyboard.call_on_reconnect())
        device.reconnect_callback.extend(self.media.call_on_reconnect())

    def start(self):
        self.media.start()
        self.keyboard.start()

        try:
            self.loop.run()
        except KeyboardInterrupt:
            self.loop.quit()
            self.media.stop()
