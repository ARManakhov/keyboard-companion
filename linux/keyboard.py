import subprocess
import ast

import dbus


class KeyboardLayoutMonitor:
    def __init__(self, device, bus):
        self.device = device
        self.bus = bus
        self.prev_layout = None
        self.layout_method = None
        self.layout_signal_match = None
        self.kde_has_getcurrent = False

        self._detect_layout_method()

        self.device.reconnect_callback.append(self.check_initial_layout)

    def _detect_layout_method(self):
        try:
            obj = self.bus.get_object("org.kde.keyboard", "/Layouts")
            iface = dbus.Interface(obj, "org.kde.KeyboardLayouts")

            try:
                iface.getCurrentLayout()
                self.kde_has_getcurrent = True
                self.layout_method = "kde"
                return
            except dbus.exceptions.DBusException:
                pass

            try:
                layouts = iface.getLayoutsList()
                if isinstance(layouts, (dbus.Array, list)) and len(layouts) > 0:
                    self.kde_has_getcurrent = False
                    self.layout_method = "kde"
                    return
            except Exception as e:
                print(f"KDE fallback failed: {e}")

        except Exception as e:
            print(f"KDE bus failed: {e}")

        try:
            obj = self.bus.get_object("org.freedesktop.IBus", "/org/freedesktop/IBus")
            iface = dbus.Interface(obj, "org.freedesktop.IBus")
            iface.GetCurrentEngine()
            self.layout_method = "ibus"
            return
        except Exception:
            pass

        try:
            r = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.input-sources", "current"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if r.returncode == 0 and r.stdout.strip():
                self.layout_method = "gnome"
                return
        except Exception:
            pass

        try:
            r = subprocess.run(
                ["setxkbmap", "-query"], capture_output=True, text=True, timeout=1
            )
            if r.returncode == 0 and "layout" in r.stdout:
                self.layout_method = "x11"
                print("[MONITOR] X11 OK")
                return
        except Exception:
            pass

    def get_current_layout(self):
        try:
            if self.layout_method == "kde":
                obj = self.bus.get_object("org.kde.keyboard", "/Layouts")
                iface = dbus.Interface(obj, "org.kde.KeyboardLayouts")

                if self.kde_has_getcurrent:
                    return str(iface.getCurrentLayout())

                idx = iface.getLayout()
                layouts = iface.getLayoutsList()
                if not isinstance(layouts, (dbus.Array, list)):
                    return None

                idx_int = int(idx)
                if not (0 <= idx_int < len(layouts)):
                    return None

                layout = layouts[idx_int]
                if isinstance(layout, (dbus.Struct, tuple, list)) and len(layout) >= 1:
                    return str(layout[0])
                return str(layout)

            elif self.layout_method == "ibus":
                obj = self.bus.get_object(
                    "org.freedesktop.IBus", "/org/freedesktop/IBus"
                )
                iface = dbus.Interface(obj, "org.freedesktop.IBus")
                engine_path = iface.GetCurrentEngine()
                if not engine_path:
                    return None
                engine_obj = self.bus.get_object("org.freedesktop.IBus", engine_path)
                engine_props = dbus.Interface(
                    engine_obj, "org.freedesktop.DBus.Properties"
                )
                name = engine_props.Get("org.freedesktop.IBus.Engine", "Name")
                return str(name) if name else str(engine_path)

            elif self.layout_method == "gnome":
                r = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.input-sources", "current"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if r.returncode != 0 or not r.stdout.strip():
                    return None
                current_str = r.stdout.strip().replace("uint32", "").strip()
                if not current_str:
                    return None
                try:
                    idx = int(current_str)
                except ValueError:
                    print(f"[!] Failed to parse current index: {current_str!r}")
                    return None

                r2 = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.input-sources", "sources"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if r2.returncode != 0 or not r2.stdout.strip():
                    return None

                sources_str = r2.stdout.strip()
                if sources_str.startswith("@as "):
                    sources_str = sources_str[4:]
                if sources_str in ("[]", "", "None"):
                    return None

                try:
                    sources = ast.literal_eval(sources_str)
                except (ValueError, SyntaxError) as e:
                    print(f"[!] Failed to parse sources: {sources_str!r}, error: {e}")
                    return None

                if not isinstance(sources, list) or not (0 <= idx < len(sources)):
                    return None

                item = sources[idx]
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    return str(item[1])
                return None

            elif self.layout_method == "x11":
                r = subprocess.run(
                    ["setxkbmap", "-query"], capture_output=True, text=True, timeout=1
                )
                if r.returncode == 0:
                    for line in r.stdout.splitlines():
                        if line.startswith("layout:"):
                            return line.split(":", 1)[1].strip()
                return None

        except Exception as e:
            print(f"Exception in get_current_layout: {e}")
            return None

    def _send_layout(self, layout):
        self.prev_layout = layout
        if hasattr(self.device, "send_keyboard_layout"):
            try:
                self.device.send_keyboard_layout(layout)
            except Exception as e:
                print(f"send_keyboard_layout FAILED: {e}")

    def check_initial_layout(self):
        layout = self.get_current_layout()
        if layout:
            self._send_layout(layout)

    def _subscribe_layout_signals(self):
        if self.layout_method == "kde" and not self.layout_signal_match:
            try:
                self.layout_signal_match = self.bus.add_signal_receiver(
                    self.on_layout_changed,
                    signal_name="layoutChanged",
                    path="/Layouts",
                    dbus_interface="org.kde.KeyboardLayouts",
                    bus_name="org.kde.keyboard",
                )
            except Exception as e:
                print(f"Layout subscribe failed: {e}")

    def on_layout_changed(self, *args):
        layout = self.get_current_layout()
        if layout and layout != self.prev_layout:
            self._send_layout(layout)

    def start(self):
        self.check_initial_layout()
        self._subscribe_layout_signals()
