"""curses UI: ↑/↓ select, Enter confirms file + player, then play."""

from __future__ import annotations

import curses
import time
from dataclasses import dataclass
from pathlib import Path

from tgplay import __version__
from tgplay.media import format_bytes, format_duration, progress_bar
from tgplay.monitor import SizeMonitor, TrackedItem
from tgplay.player import (
    PLAYER_LABELS,
    default_player_index,
    list_installed_players,
    open_downloads,
    play,
    reveal,
)
from tgplay.scanner import MediaItem, enrich, scan, select_items


POLL_SECONDS = 0.4


@dataclass
class PlayPrompt:
    item: MediaItem
    players: list[tuple[str, str]]
    player_index: int


class App:
    def __init__(
        self,
        media_dirs: list[Path],
        min_size: int,
        player: str,
        show_all: bool = False,
    ) -> None:
        self.media_dirs = media_dirs
        self.min_size = min_size
        self.player = player
        self.show_all = show_all
        self.monitor = SizeMonitor()
        self.probe_cache: dict[tuple[str, int, int], object] = {}
        self.rows: list[TrackedItem] = []
        self.index = 0
        self.prompt: PlayPrompt | None = None
        self.last_player: str | None = None
        self.status = "↑↓ select file   Enter choose player   o reveal   d Downloads   r refresh   q quit"
        self.message = ""

    def refresh(self, probe: bool = False) -> None:
        items = scan(self.media_dirs, min_size=self.min_size)
        items = enrich(items, cache=self.probe_cache)  # type: ignore[arg-type]
        items = select_items(items, show_all=self.show_all)
        self.rows = self.monitor.observe(items)
        if self.rows:
            self.index = min(self.index, len(self.rows) - 1)
        else:
            self.index = 0

    def selected(self) -> TrackedItem | None:
        if not self.rows:
            return None
        return self.rows[self.index]

    def open_play_prompt(self) -> None:
        row = self.selected()
        if row is None:
            self.message = "nothing selected"
            return
        players = list_installed_players()
        if not players:
            self.message = "no player found — install VLC: brew install --cask vlc"
            return
        preferred = self.last_player or self.player
        self.prompt = PlayPrompt(
            item=row.item,
            players=players,
            player_index=default_player_index(players, preferred=preferred),
        )
        self.message = ""

    def move_prompt_player(self, delta: int) -> None:
        if self.prompt is None or not self.prompt.players:
            return
        count = len(self.prompt.players)
        self.prompt.player_index = (self.prompt.player_index + delta) % count

    def confirm_play(self) -> None:
        if self.prompt is None:
            return
        item = self.prompt.item
        name, _binary = self.prompt.players[self.prompt.player_index]
        if item.playable is False:
            self.message = "header looks unplayable — Telegram may still be filling the start of the file"
        ok, text = play(item.path, preferred=name)
        self.last_player = name
        self.prompt = None
        self.message = text if ok else f"play failed: {text}"

    def cancel_prompt(self) -> None:
        self.prompt = None
        self.message = "cancelled — nothing started"

    def reveal_selected(self) -> None:
        row = self.selected()
        if row is None:
            self.message = "nothing to reveal"
            return
        ok, text = reveal(row.item.path)
        self.message = text if ok else f"reveal failed: {text}"


def run_curses(
    media_dirs: list[Path],
    min_size: int,
    player: str,
    show_all: bool = False,
) -> None:
    app = App(media_dirs, min_size, player, show_all=show_all)
    app.refresh(probe=True)
    curses.wrapper(lambda stdscr: _loop(stdscr, app))


def _loop(stdscr: curses.window, app: App) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(5, curses.COLOR_RED, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)

    last = 0.0
    while True:
        now = time.monotonic()
        if now - last >= POLL_SECONDS:
            app.refresh()
            last = now
        _draw(stdscr, app)
        try:
            key = stdscr.get_wch()
        except curses.error:
            time.sleep(0.05)
            continue
        if not _handle_key(app, key):
            return


def _handle_key(app: App, key: int | str) -> bool:
    if app.prompt is not None:
        if key in ("q", "Q"):
            return False
        if key in (curses.KEY_UP, "k"):
            app.move_prompt_player(-1)
        elif key in (curses.KEY_DOWN, "j"):
            app.move_prompt_player(1)
        elif key in (curses.KEY_ENTER, "\n", "\r"):
            app.confirm_play()
        elif key in (27, "\x1b", "n", "N"):
            app.cancel_prompt()
        return True

    if key in ("q", "Q"):
        return False
    if key in (curses.KEY_UP, "k"):
        app.index = max(0, app.index - 1)
    elif key in (curses.KEY_DOWN, "j"):
        if app.rows:
            app.index = min(len(app.rows) - 1, app.index + 1)
    elif key in (curses.KEY_ENTER, "\n", "\r", " "):
        app.open_play_prompt()
    elif key in ("o", "O"):
        app.reveal_selected()
    elif key in ("d", "D"):
        ok, text = open_downloads()
        app.message = text if ok else text
    elif key in ("r", "R"):
        app.refresh(probe=True)
        app.message = "refreshed"
    elif key == curses.KEY_RESIZE:
        pass
    return True


def _draw(stdscr: curses.window, app: App) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    width = max(20, width)
    _add(stdscr, 0, 0, f" tgplay {__version__} ", curses.color_pair(4) | curses.A_BOLD)
    dirs = ", ".join(_short_dir(path) for path in app.media_dirs) or "no Telegram media folder"
    _add(stdscr, 0, 14, f" {dirs}"[: width - 15], curses.color_pair(1))
    _add(stdscr, 1, 0, " Telegram Downloads", curses.A_BOLD)

    if not app.media_dirs:
        _add(stdscr, 3, 2, "Telegram media folder not found.", curses.color_pair(5))
        _add(stdscr, 4, 2, "Open Telegram, start a download, then press r.")
        _add(stdscr, 5, 2, "Or pass --media-dir PATH")
    elif not app.rows:
        _add(stdscr, 3, 2, "No large Telegram downloads right now.")
        _add(stdscr, 4, 2, "Start a video download in Telegram and it will appear here.")
    else:
        y = 3
        for i, row in enumerate(app.rows):
            block = _item_lines(row, width - 2)
            if y + len(block) >= height - 3:
                break
            selected = i == app.index
            for offset, line in enumerate(block):
                attr = curses.color_pair(4) if selected else _row_attr(row, offset)
                prefix = " ❯ " if selected and offset == 0 else "   "
                _add(stdscr, y + offset, 0, (prefix + line)[: width - 1], attr)
            y += len(block) + 1

    if app.prompt is not None:
        _draw_prompt(stdscr, app, height, width)
        status = "↑↓ player   Enter start in selected player   Esc cancel   q quit"
    else:
        status = app.status
    if app.message:
        _add(stdscr, height - 2, 1, app.message[: width - 2], curses.color_pair(3))
    _add(stdscr, height - 1, 0, status[: width - 1], curses.A_DIM)
    stdscr.refresh()


def _draw_prompt(stdscr: curses.window, app: App, height: int, width: int) -> None:
    prompt = app.prompt
    if prompt is None:
        return
    item = prompt.item
    lines = [
        " Play this file? ",
        "",
        f" {item.title}",
        f" {_prompt_size(item)}",
        f" {item.path.name}",
        "",
        " Player  (VLC recommended)",
    ]
    for index, (name, _binary) in enumerate(prompt.players):
        mark = "❯" if index == prompt.player_index else " "
        extra = "  ← recommended" if name == "vlc" else ""
        lines.append(f" {mark} {PLAYER_LABELS.get(name, name)}{extra}")
    if item.playable is False:
        lines.append("")
        lines.append(" Header not ready yet — VLC may fail until more of the file arrives.")

    box_h = len(lines) + 2
    box_w = min(width - 2, max(42, max(len(line) for line in lines) + 4))
    top = max(2, (height - box_h) // 2)
    left = max(0, (width - box_w) // 2)
    _add(stdscr, top, left, "╭" + "─" * (box_w - 2) + "╮", curses.color_pair(4) | curses.A_BOLD)
    for offset, line in enumerate(lines):
        y = top + 1 + offset
        pad = " " * max(0, box_w - 2 - len(line[: box_w - 2]))
        attr = curses.color_pair(4)
        if line.startswith(" ❯"):
            attr = curses.color_pair(4) | curses.A_BOLD
        _add(stdscr, y, left, "│" + (line[: box_w - 2] + pad) + "│", attr)
    _add(stdscr, top + box_h - 1, left, "╰" + "─" * (box_w - 2) + "╯", curses.color_pair(4) | curses.A_BOLD)


def _prompt_size(item: MediaItem) -> str:
    if item.expected_size:
        pct = f"{item.progress * 100:.0f}%" if item.progress is not None else ""
        state = "complete" if item.is_complete else "downloading"
        return f"{format_bytes(item.downloaded)} / {format_bytes(item.expected_size)}  {pct}  {state}".rstrip()
    return f"{format_bytes(item.downloaded)}  (total unknown)"


def _row_attr(row: TrackedItem, line: int) -> int:
    if line != 0:
        return curses.A_DIM
    if row.item.is_complete:
        return curses.color_pair(2)
    if row.speed_bps > 0:
        return curses.color_pair(3)
    return curses.color_pair(1)


def _item_lines(row: TrackedItem, width: int) -> list[str]:
    item = row.item
    icon = _icon(item)
    playable = "playable" if item.playable else ("not yet" if item.playable is False else "")
    duration = format_duration(item.duration)
    title = f"{icon} {item.title}"
    if duration:
        title += f"  {duration}"
    if playable:
        title += f"  · {playable}"

    downloaded = item.downloaded
    if item.expected_size:
        pct = f"{item.progress * 100:5.1f}%" if item.progress is not None else ""
        size_line = f"{format_bytes(downloaded)} / {format_bytes(item.expected_size)}  {pct}".rstrip()
    else:
        size_line = f"{format_bytes(downloaded)}  (total unknown)"
    bar_width = max(10, min(28, width - 4))
    bar = progress_bar(item.progress, bar_width)

    extra: list[str] = []
    if item.is_complete:
        extra.append("complete")
    elif row.speed_bps > 0:
        extra.append(f"↓ {format_bytes(row.speed_bps)}/s")
        if row.eta_seconds is not None:
            extra.append(f"eta {format_duration(row.eta_seconds)}")
    else:
        extra.append("paused or waiting")
    extra.append(item.account)
    return [title[:width], f"{bar}  {size_line}"[:width], "  ·  ".join(extra)[:width]]


def _icon(item: MediaItem) -> str:
    if item.media_kind == "video":
        return "🎬"
    if item.media_kind == "audio":
        return "🎵"
    if item.media_kind == "image":
        return "🖼"
    return "📄"


def _short_dir(path: Path) -> str:
    text = str(path)
    home = str(Path.home())
    if text.startswith(home):
        text = "~" + text[len(home) :]
    if "postbox/media" in text:
        return text.split("account-")[-1] if "account-" in text else "media"
    return text


def _add(stdscr: curses.window, y: int, x: int, text: str, attr: int = 0) -> None:
    height, width = stdscr.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    clipped = text[: max(0, width - x - 1)]
    try:
        stdscr.addstr(y, x, clipped, attr)
    except curses.error:
        pass


def render_list(rows: list[TrackedItem]) -> str:
    if not rows:
        return "No matching Telegram downloads."
    lines: list[str] = []
    for row in rows:
        item = row.item
        mark = "●" if not item.is_complete else "○"
        pct = f"{item.progress * 100:.0f}%" if item.progress is not None else "total unknown"
        speed = f"  ↓ {format_bytes(row.speed_bps)}/s" if row.speed_bps > 0 else ""
        expected = item.expected_size
        size_bit = (
            f"{format_bytes(item.downloaded)} / {format_bytes(expected)}"
            if expected
            else format_bytes(item.downloaded)
        )
        playable = "  playable" if item.playable else ""
        lines.append(
            f"{mark}  {item.title}  {size_bit}  {pct}{speed}{playable}"
        )
        lines.append(f"   {item.path}")
    return "\n".join(lines)
