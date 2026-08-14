"""Launch VLC / IINA / mpv against a Telegram media file."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

PLAYERS = ("vlc", "iina", "mpv")
PLAYER_LABELS = {
    "vlc": "VLC",
    "iina": "IINA",
    "mpv": "mpv",
}
PLAYER_APPS = {
    "vlc": Path("/Applications/VLC.app/Contents/MacOS/VLC"),
    "iina": Path("/Applications/IINA.app/Contents/MacOS/iina-cli"),
    "mpv": Path("/opt/homebrew/bin/mpv"),
}


def player_binary(name: str) -> str | None:
    path = shutil.which(name)
    if path:
        return path
    app = PLAYER_APPS.get(name)
    if app is not None and app.exists():
        return str(app)
    return None


def list_installed_players() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for name in PLAYERS:
        binary = player_binary(name)
        if binary:
            found.append((name, binary))
    return found


def default_player_index(players: list[tuple[str, str]], preferred: str = "auto") -> int:
    if not players:
        return 0
    if preferred != "auto":
        for index, (name, _) in enumerate(players):
            if name == preferred:
                return index
    for index, (name, _) in enumerate(players):
        if name == "vlc":
            return index
    return 0


def resolve_player(preferred: str = "auto") -> tuple[str, str] | None:
    installed = list_installed_players()
    if not installed:
        return None
    if preferred == "auto":
        return installed[default_player_index(installed, preferred="auto")]
    for name, binary in installed:
        if name == preferred:
            return name, binary
    binary = player_binary(preferred)
    if binary:
        return preferred, binary
    return None


def build_play_command(path: Path, player: str, binary: str) -> list[str]:
    target = str(path)
    if player == "mpv":
        return [
            binary,
            "--force-seekable=yes",
            "--cache=yes",
            "--demuxer-max-bytes=256MiB",
            "--keep-open=yes",
            target,
        ]
    if player == "iina":
        return [
            binary,
            "--mpv-force-seekable=yes",
            "--mpv-cache=yes",
            "--mpv-keep-open=yes",
            target,
        ]
    if player == "vlc":
        if Path("/Applications/VLC.app").exists() or binary.endswith("/VLC"):
            return ["open", "-a", "VLC", "--args", target]
        return [binary, target]
    return [binary, target]


def play(path: Path, preferred: str = "auto") -> tuple[bool, str]:
    resolved = resolve_player(preferred)
    if resolved is None:
        opened = _open_default(path)
        if opened:
            return True, "opened with the default macOS app"
        return False, "no player found — install VLC: brew install --cask vlc"
    name, binary = resolved
    command = build_play_command(path, name, binary)
    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        return False, str(exc)
    label = PLAYER_LABELS.get(name, name)
    return True, f"launched {label}"


def reveal(path: Path) -> tuple[bool, str]:
    try:
        subprocess.Popen(["open", "-R", str(path)], start_new_session=True)
    except OSError as exc:
        return False, str(exc)
    return True, "revealed in Finder"


def open_downloads() -> tuple[bool, str]:
    downloads = Path.home() / "Downloads"
    try:
        subprocess.Popen(["open", str(downloads)], start_new_session=True)
    except OSError as exc:
        return False, str(exc)
    return True, "opened Downloads"


def _open_default(path: Path) -> bool:
    try:
        subprocess.Popen(["open", str(path)], start_new_session=True)
    except OSError:
        return False
    return True
