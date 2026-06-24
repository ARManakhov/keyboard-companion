from re import L
import threading
import time

import dbus
from gi.repository import GLib


class MediaPlayerMonitor:
    def __init__(self, bus, info_callback=[], status_callback=[], progress_callback=[]):
        self.bus = bus
        self.current_player = None
        self.is_running = False
        self.paused = False
        self.meta_signal_match = None
        self.prev_progress_255 = None
        self.current_metadata = {}

        self.info_callback = info_callback
        self.status_callback = status_callback
        self.progress_callback = progress_callback

        self.position_worker = threading.Thread(target=self._position_loop, daemon=True)
        self.position_worker.start()

    def call_on_reconnect(self):
        return [self.check_initial_state, self.send_current_meta]

    def find_active_player(self):
        players = [
            name
            for name in self.bus.list_names()
            if name.startswith("org.mpris.MediaPlayer2.")
        ]
        return players[0] if players else None

    def subscribe_to_player(self, player_name):
        self.current_player = player_name
        if self.meta_signal_match:
            self.meta_signal_match.remove()
        self.meta_signal_match = self.bus.add_signal_receiver(
            self.on_properties_changed,
            bus_name=player_name,
            signal_name="PropertiesChanged",
            path="/org/mpris/MediaPlayer2",
        )
        self.check_initial_state()
        self.send_current_meta()

    def check_initial_state(self):
        try:
            player_obj = self.bus.get_object(
                self.current_player, "/org/mpris/MediaPlayer2"
            )
            iface = dbus.Interface(player_obj, "org.freedesktop.DBus.Properties")
            status = iface.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")
            metadata = iface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
            self.current_metadata = metadata
            self.handle_status_change(status)
            self.update_and_send_position(iface)
        except Exception:
            pass

    def handle_status_change(self, status):
        self.paused = status != "Playing"
        for c in self.status_callback:
            try:
                c(self.paused)
            except Exception as e:
                print(f"media status callback {c} failed {e}")

    def _position_loop(self):
        while not self.current_player:
            time.sleep(0.1)
        try:
            while True:
                player_obj = self.bus.get_object(
                    self.current_player, "/org/mpris/MediaPlayer2"
                )
                iface = dbus.Interface(player_obj, "org.freedesktop.DBus.Properties")
                if not self.paused:
                    self.update_and_send_position(iface)
                time.sleep(0.1)
        except Exception:
            pass

    def update_and_send_position(self, iface):
        try:
            metadata = self.current_metadata
            length = float(metadata.get("mpris:length", 0))
            progress_255 = 0
            if length > 0:
                position = float(iface.Get("org.mpris.MediaPlayer2.Player", "Position"))
                ratio = min(position / length, 1.0)
                progress_255 = int(ratio * 255)
            if progress_255 != self.prev_progress_255:
                for c in self.progress_callback:
                    try:
                        c(progress_255)
                    except Exception as e:
                        print(f"media progress callback {c} failed {e}")
                self.prev_progress_255 = progress_255
        except Exception:
            pass

    def send_meta(self, metadata):
        artist = ", ".join(metadata.get("xesam:artist", ["Unknown"]))
        title = metadata.get("xesam:title", "Unknown")
        art_url = metadata.get("mpris:artUrl", None)
        for c in self.info_callback:
            try:
                c(artist, title, art_url)
            except Exception as e:
                print(f"media info callback {c} failed {e}")

    def send_current_meta(self):
        try:
            player_obj = self.bus.get_object(
                self.current_player, "/org/mpris/MediaPlayer2"
            )
            iface = dbus.Interface(player_obj, "org.freedesktop.DBus.Properties")
            metadata = iface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
            self.current_metadata = metadata
            self.send_meta(metadata)
        except Exception:
            pass

    def on_properties_changed(
        self, interface, changed_properties, invalidated_properties
    ):
        if interface != "org.mpris.MediaPlayer2.Player":
            return
        if "PlaybackStatus" in changed_properties:
            self.handle_status_change(changed_properties["PlaybackStatus"])
        if "Metadata" in changed_properties:
            metadata = changed_properties["Metadata"]
            self.current_metadata = metadata
            self.send_meta(metadata)

    def on_name_owner_changed(self, name, old_owner, new_owner):
        if not name.startswith("org.mpris.MediaPlayer2."):
            return
        if new_owner == "":
            print(f"\n[-] Player {name.split('.')[-1]} was closed.")
            if name == self.current_player:
                next_player = self.find_active_player()
                if next_player:
                    self.subscribe_to_player(next_player)
                else:
                    print("[!] All players closed...")
                    self.current_player = None
                    if self.meta_signal_match:
                        self.meta_signal_match.remove()
        elif old_owner == "" and self.current_player is None:
            self.subscribe_to_player(name)

    def start(self):
        initial_player = self.find_active_player()
        if initial_player:
            self.subscribe_to_player(initial_player)

        self.bus.add_signal_receiver(
            self.on_name_owner_changed,
            signal_name="NameOwnerChanged",
        )
