"""Track download size over time to compute speed."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from tgplay.scanner import MediaItem


@dataclass(frozen=True)
class TrackedItem:
    item: MediaItem
    speed_bps: float

    @property
    def eta_seconds(self) -> float | None:
        expected = self.item.expected_size
        if not expected or self.speed_bps <= 0:
            return None
        remaining = expected - self.item.downloaded
        if remaining <= 0:
            return 0.0
        return remaining / self.speed_bps


class SizeMonitor:
    def __init__(self) -> None:
        self._prev: dict[str, tuple[int, float]] = {}

    def observe(self, items: list[MediaItem], now: float | None = None) -> list[TrackedItem]:
        clock = monotonic() if now is None else now
        tracked: list[TrackedItem] = []
        seen: set[str] = set()
        for item in items:
            seen.add(item.key)
            previous = self._prev.get(item.key)
            speed = 0.0
            if previous is not None:
                prev_size, prev_time = previous
                dt = clock - prev_time
                if dt > 0 and item.downloaded >= prev_size:
                    speed = (item.downloaded - prev_size) / dt
            self._prev[item.key] = (item.downloaded, clock)
            tracked.append(TrackedItem(item=item, speed_bps=speed))
        for key in list(self._prev):
            if key not in seen:
                del self._prev[key]
        return tracked
