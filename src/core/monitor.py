import sys


def get_monitor_class():
    if sys.platform.startswith("linux"):
        from linux.main import Monitor

        return Monitor
    print(f"Unsupported platform: {sys.platform}.")
    sys.exit(1)
