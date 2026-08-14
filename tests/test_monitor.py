from tgplay.monitor import SizeMonitor
from tgplay.scanner import MediaItem
from pathlib import Path


def _item(size: int, resource_id: str = "1") -> MediaItem:
    return MediaItem(
        path=Path(f"/tmp/{resource_id}"),
        resource_id=resource_id,
        dc_id=4,
        account="account-1",
        is_partial=True,
        is_complete=False,
        size=size,
        downloaded=size,
        expected_size=10_000,
        mtime=0.0,
        media_kind="video",
        container="matroska",
        playable=True,
    )


def test_speed_from_size_delta():
    mon = SizeMonitor()
    mon.observe([_item(1000)], now=10.0)
    tracked = mon.observe([_item(3000)], now=12.0)
    assert len(tracked) == 1
    assert tracked[0].speed_bps == 1000.0


def test_speed_zero_when_unchanged():
    mon = SizeMonitor()
    mon.observe([_item(1000)], now=1.0)
    tracked = mon.observe([_item(1000)], now=3.0)
    assert tracked[0].speed_bps == 0.0
