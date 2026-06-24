from gi.repository import GLib
from datetime import datetime


class AlignedTimer:
    def __init__(self, interval_sec: int, callback=[]):
        if interval_sec <= 0:
            raise ValueError("interval_sec must be > 0")
        self._interval = interval_sec
        self._callback = callback
        self._timer_id = None

    def _ms_to_next_boundary(self) -> int:
        now = datetime.now()
        sec_of_minute = now.second + now.microsecond / 1_000_000
        next_b = ((int(sec_of_minute) // self._interval) + 1) * self._interval

        if next_b >= 60:
            ms = int((60 - sec_of_minute) * 1000)
        else:
            ms = int((next_b - sec_of_minute) * 1000)

        return max(1, ms)

    def _on_tick(self) -> bool:
        for c in self._callback:
            try:
                c()
            except Exception as e:
                print(f"timer callback {c} failed: {e}")
        self._timer_id = GLib.timeout_add(self._ms_to_next_boundary(), self._on_tick)
        return False

    def start(self, fire_immediately: bool = False) -> None:
        self.stop()
        if fire_immediately:
            for c in self._callback:
                try:
                    c()
                except Exception as e:
                    print(f"timer callback {c} failed: {e}")
        self._timer_id = GLib.timeout_add(self._ms_to_next_boundary(), self._on_tick)

    def stop(self) -> None:
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def is_running(self) -> bool:
        return self._timer_id is not None
