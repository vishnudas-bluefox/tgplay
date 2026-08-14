"""CLI entry for tgplay."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tgplay import __version__
from tgplay.media import parse_size
from tgplay.monitor import SizeMonitor
from tgplay.scanner import enrich, scan, select_items
from tgplay.telegram import discover_media_dirs, telegram_roots
from tgplay.ui import render_list, run_curses


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tgplay",
        description="Find Telegram downloads on this Mac and play them while they fill in.",
    )
    parser.add_argument("--version", action="version", version=f"tgplay {__version__}")
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="print downloads and exit (no interactive UI)",
    )
    parser.add_argument(
        "--media-dir",
        action="append",
        type=Path,
        default=[],
        help="extra Telegram postbox/media directory (repeatable)",
    )
    parser.add_argument(
        "--min-size",
        default="2MB",
        help="ignore files smaller than this (default: 2MB)",
    )
    parser.add_argument(
        "--player",
        choices=("auto", "mpv", "iina", "vlc"),
        default="auto",
        help="preselect this player in the confirm dialog (default: auto, VLC first)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="show_all",
        help="include old leftover _partial files and finished downloads",
    )
    return parser


def collect_media_dirs(extra: list[Path]) -> list[Path]:
    dirs = discover_media_dirs(telegram_roots())
    for path in extra:
        resolved = path.expanduser()
        if resolved.is_dir() and resolved not in dirs:
            dirs.append(resolved)
    return dirs


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        min_size = parse_size(args.min_size)
    except ValueError as exc:
        print(f"tgplay: {exc}", file=sys.stderr)
        return 2

    media_dirs = collect_media_dirs(args.media_dir)
    if args.list or not sys.stdout.isatty():
        items = select_items(
            enrich(scan(media_dirs, min_size=min_size)),
            show_all=args.show_all,
        )
        rows = SizeMonitor().observe(items)
        if not media_dirs:
            print("Telegram media folder not found.", file=sys.stderr)
            print("Pass --media-dir PATH if Telegram is installed in a custom location.", file=sys.stderr)
            return 1
        print(render_list(rows))
        return 0

    try:
        run_curses(
            media_dirs,
            min_size=min_size,
            player=args.player,
            show_all=args.show_all,
        )
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
