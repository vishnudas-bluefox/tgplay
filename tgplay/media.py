"""Identify media type and format download sizes / progress."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

_UNITS = {"B": 1, "K": 1024, "KB": 1024, "M": 1024**2, "MB": 1024**2, "G": 1024**3, "GB": 1024**3}


@dataclass(frozen=True)
class Probe:
    media_kind: str
    container: str | None
    playable: bool
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    codec: str | None = None


def format_bytes(n: int | float) -> str:
    value = float(n)
    if value < 1024:
        return f"{int(value)} B"
    for unit, size in (("KB", 1024), ("MB", 1024**2), ("GB", 1024**3), ("TB", 1024**4)):
        if value < size * 1024 or unit == "TB":
            return f"{value / size:.2f} {unit}"
    return f"{value:.0f} B"


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return ""
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def parse_size(text: str) -> int:
    raw = text.strip().upper().replace(" ", "")
    match = re.fullmatch(r"([0-9]*\.?[0-9]+)([KMGTB]I?B?)?", raw)
    if not match:
        raise ValueError(f"invalid size: {text}")
    number = float(match.group(1))
    unit = match.group(2) or "B"
    unit = unit.replace("I", "")
    if unit not in _UNITS:
        raise ValueError(f"invalid size unit: {text}")
    return int(number * _UNITS[unit])


def progress_bar(ratio: float | None, width: int = 24) -> str:
    if width <= 0:
        return ""
    if ratio is None:
        return "?" * width
    filled = int(round(max(0.0, min(1.0, ratio)) * width))
    filled = min(width, max(0, filled))
    return "█" * filled + "░" * (width - filled)


def sniff_header(head: bytes) -> Probe:
    if len(head) >= 4 and head[:4] == b"\x1aE\xdf\xa3":
        return Probe("video", "matroska", True)
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return Probe("video", "mp4", True)
    if head.startswith(b"RIFF") and b"AVI" in head[:16]:
        return Probe("video", "avi", True)
    if head.startswith(b"RIFF") and b"WAVE" in head[:16]:
        return Probe("audio", "wav", True)
    if head.startswith(b"OggS"):
        return Probe("audio", "ogg", True)
    if head.startswith(b"fLaC"):
        return Probe("audio", "flac", True)
    if head.startswith(b"ID3") or head[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"}:
        return Probe("audio", "mp3", True)
    if head.startswith(b"%PDF"):
        return Probe("document", "pdf", False)
    if head.startswith(b"\x89PNG"):
        return Probe("image", "png", False)
    if head.startswith(b"\xff\xd8\xff"):
        return Probe("image", "jpeg", False)
    if head.startswith(b"GIF8"):
        return Probe("image", "gif", True)
    if not head or set(head[:32]) <= {0}:
        return Probe("unknown", None, False)
    return Probe("unknown", None, False)


def sniff_file(path: Path) -> Probe:
    try:
        with path.open("rb") as handle:
            head = handle.read(64)
    except OSError:
        return Probe("unknown", None, False)
    base = sniff_header(head)
    probed = _ffprobe(path)
    if probed is None:
        return base
    return Probe(
        media_kind=probed.media_kind or base.media_kind,
        container=probed.container or base.container,
        playable=True if probed.playable else base.playable,
        duration=probed.duration,
        width=probed.width,
        height=probed.height,
        codec=probed.codec,
    )


def _ffprobe(path: Path) -> Probe | None:
    binary = shutil.which("ffprobe")
    if binary is None:
        return None
    try:
        result = subprocess.run(
            [
                binary,
                "-v",
                "error",
                "-show_entries",
                "format=format_name,duration:stream=codec_type,codec_name,width,height",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    streams = payload.get("streams") or []
    fmt = payload.get("format") or {}
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if video:
        kind = "video"
        codec = video.get("codec_name")
        width = video.get("width")
        height = video.get("height")
    elif audio:
        kind = "audio"
        codec = audio.get("codec_name")
        width = height = None
    else:
        return None
    duration = fmt.get("duration")
    try:
        duration_f = float(duration) if duration is not None else None
    except (TypeError, ValueError):
        duration_f = None
    container = (fmt.get("format_name") or "").split(",")[0] or None
    return Probe(
        media_kind=kind,
        container=container,
        playable=True,
        duration=duration_f,
        width=int(width) if width else None,
        height=int(height) if height else None,
        codec=codec,
    )
