"""Locate Telegram Desktop / Telegram for macOS media directories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

NATIVE_BUNDLE = "6N38VWS5BX.ru.keepcoder.Telegram"
DESKTOP_SUPPORT = "Telegram Desktop"


@dataclass(frozen=True)
class ResourceName:
    kind: str
    dc_id: int
    resource_id: str
    is_partial: bool


def telegram_roots(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    candidates = [
        home / "Library/Group Containers" / NATIVE_BUNDLE,
        home / "Library/Application Support" / DESKTOP_SUPPORT,
    ]
    return [path for path in candidates if path.is_dir()]


def discover_media_dirs(roots: list[Path] | None = None) -> list[Path]:
    roots = roots if roots is not None else telegram_roots()
    found: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        patterns = (
            "*/account-*/postbox/media",
            "account-*/postbox/media",
        )
        for pattern in patterns:
            for media in root.glob(pattern):
                resolved = media.resolve()
                if resolved in seen or not media.is_dir():
                    continue
                seen.add(resolved)
                found.append(media)
    return found


def parse_resource_name(name: str) -> ResourceName | None:
    if name.endswith(".meta") or name.endswith(".partial.meta"):
        return None
    partial = name.endswith("_partial")
    stem = name[: -len("_partial")] if partial else name
    if not stem.startswith("telegram-cloud-document-"):
        return None
    rest = stem[len("telegram-cloud-document-") :]
    dc_str, sep, resource_id = rest.partition("-")
    if not sep or not dc_str.isdigit() or not resource_id.isdigit():
        return None
    return ResourceName(
        kind="document",
        dc_id=int(dc_str),
        resource_id=resource_id,
        is_partial=partial,
    )


def account_label(media_dir: Path) -> str:
    for part in media_dir.parts:
        if part.startswith("account-"):
            flavor = "appstore" if "appstore" in media_dir.parts else "stable"
            return f"{flavor}/{part}"
    return str(media_dir)
