"""Scan Telegram media folders for downloadable / playable files."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from pathlib import Path

from tgplay.media import Probe, sniff_file
from tgplay.telegram import account_label, parse_resource_name

ACTIVE_MAX_AGE = 48 * 3600
RECENT_COMPLETE_AGE = 24 * 3600


@dataclass(frozen=True)
class PartialMeta:
    expected_size: int | None
    downloaded_size: int | None


@dataclass(frozen=True)
class MediaItem:
    path: Path
    resource_id: str
    dc_id: int
    account: str
    is_partial: bool
    is_complete: bool
    size: int
    downloaded: int
    expected_size: int | None
    mtime: float
    media_kind: str = "unknown"
    container: str | None = None
    playable: bool | None = None
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    codec: str | None = None

    @property
    def key(self) -> str:
        return f"{self.account}:{self.resource_id}"

    @property
    def progress(self) -> float | None:
        if not self.expected_size:
            return 1.0 if self.is_complete else None
        if self.expected_size <= 0:
            return None
        return min(1.0, max(0.0, self.downloaded / self.expected_size))

    @property
    def title(self) -> str:
        bits: list[str] = []
        if self.codec:
            bits.append(self.codec.upper())
        if self.width and self.height:
            bits.append(f"{self.width}×{self.height}")
        if self.container and not bits:
            bits.append(self.container)
        if not bits:
            kind = self.media_kind if self.media_kind != "unknown" else "document"
            bits.append(kind)
        bits.append(f"#{self.resource_id[-6:]}")
        return " · ".join(bits)


def parse_partial_meta(data: bytes) -> PartialMeta:
    if len(data) < 36:
        return PartialMeta(None, None)
    flag = int.from_bytes(data[8:12], "little")
    if flag != 1:
        return PartialMeta(None, None)
    expected = int.from_bytes(data[12:20], "little")
    downloaded = int.from_bytes(data[28:36], "little")
    if expected <= 0:
        expected_out = None
    else:
        expected_out = expected
    if downloaded < 0:
        downloaded_out = None
    else:
        downloaded_out = downloaded
    return PartialMeta(expected_out, downloaded_out)


def _read_meta(path: Path) -> PartialMeta:
    meta_path = path.with_name(path.name + ".meta")
    if not meta_path.is_file():
        return PartialMeta(None, None)
    try:
        return parse_partial_meta(meta_path.read_bytes())
    except OSError:
        return PartialMeta(None, None)


def _apply_probe(item: MediaItem, probe: Probe) -> MediaItem:
    return replace(
        item,
        media_kind=probe.media_kind,
        container=probe.container,
        playable=probe.playable,
        duration=probe.duration,
        width=probe.width,
        height=probe.height,
        codec=probe.codec,
    )


def scan_media_dir(media_dir: Path, min_size: int = 2 * 1024 * 1024) -> list[MediaItem]:
    grouped: dict[str, list[Path]] = {}
    try:
        entries = list(media_dir.iterdir())
    except OSError:
        return []

    for path in entries:
        if not path.is_file():
            continue
        parsed = parse_resource_name(path.name)
        if parsed is None:
            continue
        grouped.setdefault(parsed.resource_id, []).append(path)

    items: list[MediaItem] = []
    account = account_label(media_dir)
    for resource_id, paths in grouped.items():
        partials = [p for p in paths if p.name.endswith("_partial")]
        completes = [p for p in paths if not p.name.endswith("_partial")]
        primary = partials[0] if partials else completes[0]
        try:
            stat = primary.stat()
        except OSError:
            continue

        complete_stat = None
        if completes:
            try:
                complete_stat = completes[0].stat()
            except OSError:
                complete_stat = None

        same_inode = (
            complete_stat is not None and complete_stat.st_ino == stat.st_ino
        )
        meta = _read_meta(partials[0]) if partials else PartialMeta(None, None)
        expected = meta.expected_size
        downloaded = meta.downloaded_size if meta.downloaded_size is not None else stat.st_size
        if expected is None and complete_stat is not None:
            expected = complete_stat.st_size
        is_complete = bool(
            completes
            and (
                same_inode
                or (expected is not None and downloaded >= expected)
                or not partials
            )
        )
        if is_complete and complete_stat is not None:
            display = completes[0]
            size = complete_stat.st_size
            downloaded = size
            if expected is None:
                expected = size
            mtime = complete_stat.st_mtime
            is_partial = False
        else:
            display = primary
            size = stat.st_size
            mtime = stat.st_mtime
            is_partial = display.name.endswith("_partial")

        parsed = parse_resource_name(display.name)
        if parsed is None:
            continue

        interesting = (
            size >= min_size
            or (expected is not None and expected >= min_size)
            or (not is_complete and downloaded >= min_size)
        )
        if not interesting:
            continue

        items.append(
            MediaItem(
                path=display,
                resource_id=resource_id,
                dc_id=parsed.dc_id,
                account=account,
                is_partial=is_partial,
                is_complete=is_complete,
                size=size,
                downloaded=downloaded,
                expected_size=expected,
                mtime=mtime,
            )
        )

    items.sort(key=lambda item: (item.is_complete, -item.downloaded, -item.mtime))
    return items


def scan(media_dirs: list[Path], min_size: int = 2 * 1024 * 1024) -> list[MediaItem]:
    items: list[MediaItem] = []
    for media_dir in media_dirs:
        items.extend(scan_media_dir(media_dir, min_size=min_size))
    items.sort(key=lambda item: (item.is_complete, -item.downloaded, -item.mtime))
    return items


def is_active_download(item: MediaItem, now: float | None = None) -> bool:
    clock = time.time() if now is None else now
    if item.is_complete or item.expected_size is None:
        return False
    if item.downloaded >= item.expected_size:
        return False
    return (clock - item.mtime) <= ACTIVE_MAX_AGE


def select_items(
    items: list[MediaItem],
    *,
    show_all: bool = False,
    now: float | None = None,
) -> list[MediaItem]:
    if show_all:
        return items
    clock = time.time() if now is None else now
    active = [item for item in items if is_active_download(item, now=clock)]
    recent = [
        item
        for item in items
        if item.is_complete and (clock - item.mtime) <= RECENT_COMPLETE_AGE
    ]
    chosen = active + recent
    if chosen:
        chosen.sort(key=lambda item: (item.is_complete, -item.downloaded, -item.mtime))
        return chosen
    return items[:20]


def enrich(items: list[MediaItem], cache: dict[tuple[str, int, int], Probe] | None = None) -> list[MediaItem]:
    cache = cache if cache is not None else {}
    enriched: list[MediaItem] = []
    for item in items:
        key = (str(item.path), item.size, int(item.mtime))
        probe = cache.get(key)
        if probe is None:
            probe = sniff_file(item.path)
            cache[key] = probe
        enriched.append(_apply_probe(item, probe))
    return enriched
