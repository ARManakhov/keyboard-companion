import sys
from device import Device
from clock import AlignedTimer

TARGET_VID = 0xE126
TARGET_PID = 0x0051
TARGET_INT = 1
INTERVAL_SEC = 30


def main():
    found_platform = False
    if sys.platform.startswith("linux"):
        found_platform = True
        from linux.main import Monitor
    if not found_platform:
        print(f"Unsupported platform: {sys.platform}. ")
        sys.exit(1)

    device = Device(TARGET_VID, TARGET_PID, TARGET_INT)
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


if __name__ == "__main__":
    main()
