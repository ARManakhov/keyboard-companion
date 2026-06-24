from logging import debug
import time
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageOps
import hid
import threading
import queue
from font import generate_and_load_qff_auto


class Commands(Enum):
    ASK_CAPABILITIES = 1
    TIME = 2
    LANG = 3
    VOLUME = 4
    LAYOUT = 5
    MEDIA_ARTIST = 6
    MEDIA_TITLE = 7
    MEDIA_CONTROL = 8
    MEDIA_COVER = 9
    ASK_SCREEN_PAGE = 10
    MEDIA_FONT = 11


class DeviceInfo:
    def __init__(self, dev) -> None:
        self.vid = dev.get("vendor_id", 0)
        self.pid = dev.get("product_id", 0)
        self.interface = dev.get("interface_number", -1)
        self.manufacturer = dev.get("manufacturer_string") or "N/A"
        self.product = dev.get("product_string") or "N/A"

        self.path = dev.get("path", b"")
        self.path_str = self.path.decode("utf-8", errors="replace")

    def __str__(self) -> str:
        return f"{self.manufacturer} {self.product} {self.vid:04X}:{self.pid:04X}:{self.interface}"


VIAL_SERIAL_MAGIC = "vial:f64c2b3c"
VIBL_SERIAL_MAGIC = "vibl:d4f8159c"


def probe_device(
    dev_info: DeviceInfo, packet_len: int = 32, timeout_ms: int = 100
) -> bool:
    try:
        dev = hid.device()
        dev.open_path(dev_info.path)
        try:
            msg = bytes([0xAA]) + bytes(packet_len - 1)
            dev.write(msg)

            resp = dev.read(packet_len, timeout_ms=timeout_ms)

            if resp and len(resp) > 0 and resp[0] == 0xAA:
                return True
        finally:
            dev.close()

    except Exception:
        pass

    return False


def get_devices() -> List[DeviceInfo]:
    devices = hid.enumerate()
    if not devices:
        return []

    candidate_devices = []

    for dev in devices:
        usage_page = dev.get("usage_page", 0)
        usage = dev.get("usage", 0)
        serial = dev.get("serial_number", "")

        if (usage_page == 0xFF60 and usage == 0x61) or (VIAL_SERIAL_MAGIC in serial):
            dev_info = DeviceInfo(dev)
            if probe_device(dev_info):
                candidate_devices.append(dev_info)

    return candidate_devices


class Device:
    def __init__(
        self,
        vid,
        pid,
        interface,
        disconnect_callback=[],
        reconnect_callback=[],
        capabilitis_callback=[],
        package_size=32,
        debug=False,
    ):
        self.vid = vid
        self.pid = pid
        self.interface = interface
        self.package_size = package_size

        self.debug = debug

        self.command_description = dict()
        self.command_description[Commands.ASK_CAPABILITIES] = 0xAA

        self.device = None
        self._lock = threading.RLock()
        self._reconnecting = False
        self._closed = False
        self.write_queue = queue.Queue()

        self.disconnect_callback = []
        self.reconnect_callback = [
            self._clean_prev_data,
            self._send_ask_capabilities,
            self.send_time,
        ]
        self.capabilitis_callback = []
        self.disconnect_callback.extend(disconnect_callback)
        self.reconnect_callback.extend(reconnect_callback)
        self.capabilitis_callback.extend(capabilitis_callback)

        self.write_task = threading.Thread(target=self._write, daemon=True)
        self.write_task.start()

        self.prev_media_artist = None
        self.prev_media_name = None
        self.prev_media_cover_bytes = None
        self.prev_media_cover_url = None
        self.prev_media_font_glyphs = None

        self._reconnect()

    def _connect(self):
        if self.device is not None:
            return True

        devices = hid.enumerate(self.vid, self.pid)
        for d in devices:
            if d.get("interface_number") != self.interface:
                continue
            try:
                dev = hid.device()
                dev.open_path(d["path"])
                self.device = dev
                print(
                    f"[USB] Connected: VID {hex(self.vid)}, PID {hex(self.pid)}, Int {self.interface}"
                )
                return True
            except Exception as e:
                print(f"[USB] Connection error: {e}")
        return False

    def _reconnect(self):
        if self._reconnecting:
            while self._reconnecting and not self._closed:
                time.sleep(0.1)
            return

        self._reconnecting = True
        for callback in self.disconnect_callback:
            try:
                callback()
            except Exception as e:
                print(f"[USB] Disonnect callback error: {e}")
        try:
            with self._lock:
                if self.device:
                    try:
                        self.device.close()
                    except Exception:
                        pass
                    self.device = None

            print("[USB] Connection lost. Reconnecting...")
            while not self._closed:
                with self._lock:
                    if self._connect():
                        break
                time.sleep(1)
        finally:
            self._reconnecting = False

        with self._lock:
            if self.device is not None:
                for callback in self.reconnect_callback:
                    try:
                        callback()
                    except Exception as e:
                        print(f"[USB] Reconnect callback error: {e}")

    def close(self):
        self._closed = True
        with self._lock:
            if self.device:
                try:
                    self.device.close()
                except Exception:
                    pass
                self.device = None

    def pad_package(self, package):
        if isinstance(package, list):
            needed = self.package_size - (len(package) - 1)
            if needed > 0:
                package += [0x00] * needed
        elif isinstance(package, bytearray):
            while len(package) < self.package_size:
                package.append(0)
        return package

    def _send_ask_capabilities(self):
        packet = [Commands.ASK_CAPABILITIES]
        self._write_blocking(packet)

    def _clean_prev_data(self):
        self.prev_media_artist = None
        self.prev_media_name = None
        self.prev_media_cover_bytes = None
        self.prev_media_cover_url = None
        self.prev_media_font_glyphs = None

    def _fill_command_descriptions(self, confirmation):
        for cmd in Commands:
            self.command_description[cmd] = confirmation[cmd.value]
        if self.debug:
            print(self.command_description)
        capabilities = []
        for i in self.command_description.keys():
            if self.command_description[i] != 0x00:
                capabilities.append(i)
        for callback in self.capabilitis_callback:
            callback(capabilities)

    def _wait_for_device(self):
        while not self._closed:
            with self._lock:
                dev = self.device
            if dev is not None:
                return True
            self._reconnect()
            time.sleep(0.05)
        return False

    def preprocess_command(self, package):
        command = package[0]
        if isinstance(command, Commands):
            if command not in self.command_description:
                package[0] = 0x00
            package[0] = self.command_description[package[0]]
        if package[0] == 0x00 and self.debug:
            print(f"{command} will be skipped (not in dev capabilities)")
        return package

    def _send_and_confirm(self, package):
        package = self.preprocess_command(package)
        if package[0] == 0x00:
            return True
        package = self.pad_package(package)
        try:
            with self._lock:
                dev = self.device

            if dev is None:
                return False

            dev.write(package)

            confirmed = False
            for _ in range(50):
                try:
                    confirmation = dev.read(self.package_size, 20)
                except Exception:
                    raise

                if (
                    confirmation
                    and len(confirmation) > 0
                    and (
                        confirmation[0] == 240
                        or confirmation[0]
                        == self.command_description[Commands.ASK_CAPABILITIES]
                    )
                ):
                    if (
                        confirmation[0]
                        == self.command_description[Commands.ASK_CAPABILITIES]
                    ):
                        self._fill_command_descriptions(confirmation)
                    if self.debug:
                        print(f"Send {package[0]:X} package")
                    confirmed = True
                    break

            if not confirmed:
                raise Exception("No confirmation received")

            return True

        except Exception as e:
            print(f"error on sending {package[0]:X} package: {e}")

            with self._lock:
                if self.device:
                    try:
                        self.device.close()
                    except Exception:
                        pass
                    self.device = None

            self._reconnect()
            return False

    def _write_blocking(self, package):
        if not self._wait_for_device():
            return

        if self._closed:
            return

        if not self._send_and_confirm(package):
            self.write_queue.put(package)

    def _write(self):
        while not self._closed:
            try:
                package = self.write_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if not self._wait_for_device():
                break

            if self._closed:
                break

            if not self._send_and_confirm(package):
                self.write_queue.put(package)

    def write(self, package):
        if not self._closed:
            self.write_queue.put(package)

    def write_long(self, raw_bytes, report_id):
        chunk_size = self.package_size - 3
        total_bytes = len(raw_bytes)
        package_idx = 0

        for i in range(0, total_bytes, chunk_size):
            chunk = raw_bytes[i : i + chunk_size]

            package = [
                report_id,
                (package_idx >> 8) & 0xFF,
                package_idx & 0xFF,
            ] + list(chunk)

            self.write(package)
            package_idx += 1

        if self.debug:
            print(f"Sent large package {report_id} with {package_idx} hid packages")

    @staticmethod
    def prepare_str(text, report_id: int | Commands = 0x00):
        raw_bytes = text.encode("utf-8", errors="ignore")

        if len(raw_bytes) >= 30:
            while True:
                test_bytes = (text + "..").encode("utf-8", errors="ignore")
                if len(test_bytes) <= 30:
                    raw_bytes = test_bytes
                    break
                text = text[:-1]

        length = len(raw_bytes)
        package = [report_id, length] + list(raw_bytes)

        return package

    @staticmethod
    def prepare_image(image_path, target_size=76):  # only rgb565 for now
        img = Image.open(image_path.replace("file://", "")).convert("RGB")
        img = ImageOps.pad(img, (target_size, target_size), color=(0, 0, 0))

        raw_bytes = []

        for y in range(target_size):
            for x in range(target_size):
                r, g, b = img.getpixel((x, y))
                r_5 = (r >> 3) & 0x1F
                g_6 = (g >> 2) & 0x3F
                b_5 = (b >> 3) & 0x1F

                rgb565 = (r_5 << 11) | (g_6 << 5) | b_5

                raw_bytes.append((rgb565 >> 8) & 0xFF)
                raw_bytes.append(rgb565 & 0xFF)

        return raw_bytes

    def send_playback_progress(self, progress):
        package = [
            Commands.MEDIA_CONTROL,
            0x02,
            progress,
        ]
        self.write(package)

    def send_playback_status(self, paused: bool):
        package = [Commands.MEDIA_CONTROL, 0x01, int(paused)]
        self.write(package)

    def send_font_length(self, len):
        package = [
            Commands.MEDIA_CONTROL,
            0x03,
            (len >> 8) & 0xFF,
            len & 0xFF,
        ]
        self.write(package)

    def send_media_font_for_text(self, text):
        try:
            unicode_glyphs = set(text)
            unicode_glyphs.add(".")
            if unicode_glyphs == self.prev_media_font_glyphs:
                return
            self.prev_media_font_glyphs = unicode_glyphs

            if all(ord(c) < 128 for c in unicode_glyphs):
                self.send_font_length(0)
                return

            custom_font = generate_and_load_qff_auto(
                unicode_glyphs="".join(unicode_glyphs),
            )
            self.send_font_length(len(custom_font))
            self.write_long(custom_font, Commands.MEDIA_FONT)
        except Exception as e:
            import traceback

            print(f"error on generating font {e}\n{traceback.format_exc()}")

    def send_media_info(self, artist, name):
        self.send_media_artist(artist)
        self.send_media_name(name)
        self.send_media_font_for_text(artist + name)

    def send_media_artist(self, artist):
        if self.prev_media_artist == artist:
            return
        self.prev_media_artist = artist
        artist_package = self.prepare_str(artist, Commands.MEDIA_ARTIST)
        self.write(artist_package)

    def send_media_name(self, name):
        if self.prev_media_name == name:
            return
        self.prev_media_name = name
        name_package = self.prepare_str(name, Commands.MEDIA_TITLE)
        self.write(name_package)

    def clean_media_cover(self):
        start_packet = [Commands.MEDIA_CONTROL, 0x00, 0x01]
        self.write(start_packet)

    def send_media_cover(self, cover):
        if self.prev_media_cover_url == cover:
            return
        self.prev_media_cover_url = cover
        if cover:
            if self.debug:
                print(cover)
            try:
                raw_img = self.prepare_image(cover)
                if self.prev_media_cover_bytes == raw_img:
                    return
                self.prev_media_cover_bytes = raw_img
                self.clean_media_cover()
                self.write_long(
                    raw_img,
                    Commands.MEDIA_COVER,
                )
            except Exception as e:
                print(e)

    def send_time(self):
        current_hour = time.localtime().tm_hour
        current_minute = time.localtime().tm_min

        current_day = time.localtime().tm_mday
        current_day_week = time.localtime().tm_wday
        current_month = time.localtime().tm_mon
        current_year = time.localtime().tm_year

        packet = [
            Commands.TIME,
            current_hour,
            current_minute,
            current_day,
            current_day_week,
            current_month,
        ] + list(current_year.to_bytes(2, byteorder="big"))
        self.write(packet)

    def send_keyboard_layout(self, layout: str):
        packet = self.prepare_str(layout, Commands.LANG)
        self.write(packet)
