import argparse
from device import Device, get_devices
from clock import AlignedTimer
from gui import init as gui_init
from uitls import get_monitor_class

INTERVAL_SEC = 30




def cmd_gui(args):
    gui_init()


def cmd_list(args):
    print(
        f"{'VID'}  {'PID':>4}  {'IF':>4}  {'Manufacturer':<20}  {'Product':<25}  {'Path'}"
    )
    for d in get_devices():
        print(
            f"{d.vid:04X}  {d.pid:04X}  {d.interface:>3}  {d.manufacturer[:18]:<20}  {d.product[:23]:<25}  {d.path}"
        )


def cmd_connect(args):
    vid = args.vid
    pid = args.pid
    interface = args.interface
    verbose = args.verbose

    Monitor = get_monitor_class()

    device = Device(vid, pid, interface, debug=verbose)
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
    parser_connect.add_argument(
        "--verbose", type=bool, default=False, help="be more talkative"
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
