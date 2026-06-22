import threading
import time

import dbus
from gi.repository import GLib


class MediaPlayerMonitor:
    def __init__(self, device, bus):
        self.device = device
        self.bus = bus
        self.current_player = None
        self.position_timer = None
        self.is_running = False
        self.paused = False
        self.meta_signal_match = None
        self.prev_progress_255 = None

        self.device.reconnect_callback.append(self.check_initial_state)
        self.device.reconnect_callback.append(self.send_current_meta)

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
            self.handle_status_change(status)
            self.update_and_send_position(iface)
        except Exception:
            pass

    def handle_status_change(self, status):
        self.paused = status != "Playing"
        self.start_position_loop()
        self.device.send_playback_status(self.paused)

    def start_position_loop(self):
        if not self.is_running:
            self.is_running = True
            self.position_timer = threading.Thread(
                target=self._position_loop, daemon=True
            )
            self.position_timer.start()

    def stop_position_loop(self):
        self.is_running = False
        if self.position_timer:
            self.position_timer.join(timeout=0.2)
            self.position_timer = None

    def _position_loop(self):
        try:
            player_obj = self.bus.get_object(
                self.current_player, "/org/mpris/MediaPlayer2"
            )
            iface = dbus.Interface(player_obj, "org.freedesktop.DBus.Properties")
            while self.is_running and not self.paused:
                self.update_and_send_position(iface)
                time.sleep(1.0)
            self.is_running = False
        except Exception:
            self.is_running = False

    def update_and_send_position(self, iface):
        try:
            metadata = iface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
            length = float(metadata.get("mpris:length", 0))
            if length > 0:
                position = float(iface.Get("org.mpris.MediaPlayer2.Player", "Position"))
                ratio = min(position / length, 1.0)
                progress_255 = int(ratio * 255)
                if progress_255 != self.prev_progress_255:
                    self.device.send_playback_progress(progress_255)
                    self.prev_progress_255 = progress_255
        except Exception:
            pass

    def send_meta(self, metadata):
        artist = ", ".join(metadata.get("xesam:artist", ["Unknown"]))
        title = metadata.get("xesam:title", "Unknown")
        art_url = metadata.get("mpris:artUrl", None)
        self.device.send_media_info(artist, title)
        self.device.send_media_cover(art_url)
        self.start_position_loop()

    def send_current_meta(self):
        try:
            player_obj = self.bus.get_object(
                self.current_player, "/org/mpris/MediaPlayer2"
            )
            iface = dbus.Interface(player_obj, "org.freedesktop.DBus.Properties")
            metadata = iface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
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
            self.send_meta(changed_properties["Metadata"])

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
