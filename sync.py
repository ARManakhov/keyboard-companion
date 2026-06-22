import sys
import argparse
from device import Device
from clock import AlignedTimer
import hid

INTERVAL_SEC = 30


def get_monitor_class():
    if sys.platform.startswith("linux"):
        from linux.main import Monitor

        return Monitor
    print(f"Unsupported platform: {sys.platform}.")
    sys.exit(1)


def cmd_gui(args):
    print("placeholder")


def cmd_list(args):
    devices = hid.enumerate()

    if not devices:
        print("No HID devices found.")
        return

    print(
        f"{'VID'}  {'PID':>4}  {'IF':>4}  {'Manufacturer':<20}  {'Product':<25}  {'Path'}"
    )

    for dev in devices:
        vid = dev.get("vendor_id", 0)
        pid = dev.get("product_id", 0)
        interface = dev.get("interface_number", -1)
        manufacturer = dev.get("manufacturer_string") or "N/A"
        product = dev.get("product_string") or "N/A"
        path = dev.get("path", b"").decode("utf-8", errors="replace")

        manufacturer = manufacturer[:18]
        product = product[:23]

        print(
            f"{vid:04X}  {pid:04X}  {interface:>3}  {manufacturer:<20}  {product:<25}  {path}"
        )


def cmd_connect(args):
    vid = args.vid
    pid = args.pid
    interface = args.interface

    Monitor = get_monitor_class()

    device = Device(vid, pid, interface)
    if not device:
        print("Device not found.")
        return

    timer = AlignedTimer(INTERVAL_SEC, device.send_time)

    try:
        monitor = Monitor(device)
        timer.start(fire_immediately=True)
        monitor.start()
    finally:
        timer.stop()
        device.close()


def main():
    parser = argparse.ArgumentParser(description="Device monitor and controller")
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    parser_list = subparsers.add_parser("list", help="Show available devices")

    parser_gui = subparsers.add_parser("gui", help="Run in GUI mode")

    parser_connect = subparsers.add_parser("connect", help="Connect to device")
    parser_connect.add_argument(
        "--vid",
        type=lambda x: int(x, 0),
        required=True,
        help="Vendor ID (hex: 0xE126 or decimal: 57638)",
    )
    parser_connect.add_argument(
        "--pid",
        type=lambda x: int(x, 0),
        required=True,
        help="Product ID (hex: 0x0051 or decimal: 81)",
    )
    parser_connect.add_argument(
        "--interface", type=int, default=1, help="Interface number (by default: 1)"
    )

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "connect":
        cmd_connect(args)
    elif args.command == "gui":
        cmd_gui(args)


if __name__ == "__main__":
    main()
