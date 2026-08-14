# tgplay

Monitor Telegram downloads on macOS and play them from the terminal **while they are still arriving**.

Created by [Vishnudas-bluefox](https://github.com/vishnudas-bluefox)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](#requirements)

Telegram for Mac writes in-progress files as `telegram-cloud-document-…_partial` inside its Group Container. **tgplay** finds those files, shows live size and speed, then asks you to confirm the file and pick a player before anything launches.

**VLC is first and recommended.** IINA and mpv appear if they are installed.

```
 tgplay 0.1.0   15012036675620673419/postbox/media
 Telegram Downloads

 ❯ 🎬 H264 · 1280×536 · #431659  1h 12m  · playable
   ████░░░░░░░░░░░░░░░░░░░░░░░░  33.00 MB / 1.41 GB   2.3%
   ↓ 12.1 MB/s  ·  eta 1m 52s  ·  stable/account-…

   🎬 HEVC · 1620×1080 · #670460  2h 08m  · playable
   ████████████████████████████  2.93 GB / 2.93 GB  100%
   complete  ·  stable/account-…

 ↑↓ select file   Enter choose player   o reveal   q quit
```

No Telegram API. No login. No extra daemon. It only reads local cache files on your Mac.

## Features

- Finds native Telegram for Mac media automatically (`6N38VWS5BX.ru.keepcoder.Telegram`)
- Lists active `_partial` downloads and recently finished large files
- Live progress, speed, ETA, and a playability hint
- Confirm the selected file, then choose **VLC / IINA / mpv** before playback
- Reveal the file in Finder or open `~/Downloads`
- `--list` mode for scripts and quick checks

## Requirements

- macOS
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or Python 3.10+
- A player: [VLC](https://www.videolan.org/vlc/) (recommended), or [IINA](https://iina.io/) / [mpv](https://mpv.io/)
- Optional: [ffmpeg](https://ffmpeg.org/) / `ffprobe` for duration and codec labels

```bash
brew install --cask vlc
# optional extras
brew install --cask iina
brew install mpv ffmpeg
```

## Install (macOS)

The usual path is Homebrew. This puts `tgplay` on your PATH so it works from any terminal:

```bash
brew install vishnudas-bluefox/tap/tgplay
```

That one line taps the repo and installs the formula. After that:

```bash
tgplay
```

If you already tapped once, later upgrades are just:

```bash
brew upgrade tgplay
```

You still need a player. VLC is recommended:

```bash
brew install --cask vlc
```

### From source

```bash
git clone https://github.com/vishnudas-bluefox/tgplay.git
cd tgplay
uv sync
uv run tgplay
```

With pip, from the repo:

```bash
python3 -m pip install .
tgplay
```

## Run

```bash
uv run tgplay
```

Other entry points:

```bash
uv run python tgplay.py
uv run python -m tgplay
uv run tgplay --list
```

Start a video download in Telegram, highlight it with ↑/↓, press Enter, pick **VLC**, then Enter again to play.

### Keys

| Key | Action |
| --- | --- |
| ↑ / ↓ or `k` / `j` | Move file selection |
| Enter or Space | Open confirm + player picker |
| ↑ / ↓ in picker | Choose VLC / IINA / mpv |
| Enter in picker | Start the selected player |
| Esc or `n` | Cancel, do not play |
| `o` | Reveal the file in Finder |
| `d` | Open `~/Downloads` |
| `r` | Rescan Telegram folders |
| `q` | Quit |

### Options

```bash
uv run tgplay --list
uv run tgplay --all
uv run tgplay --player vlc
uv run tgplay --min-size 8MB
uv run tgplay --media-dir "/path/to/postbox/media"
```

| Flag | Meaning |
| --- | --- |
| `-l`, `--list` | Print downloads and exit |
| `--all` | Include stale leftover `_partial` files and older finished downloads |
| `--player` | Preselect `vlc`, `iina`, `mpv`, or `auto` (VLC first) |
| `--min-size` | Ignore files smaller than this (default `2MB`) |
| `--media-dir` | Extra Telegram `postbox/media` folder (repeatable) |

## How it works

Telegram for Mac stores downloads here:

```text
~/Library/Group Containers/6N38VWS5BX.ru.keepcoder.Telegram/
  {stable,appstore}/account-*/postbox/media/telegram-cloud-document-*_partial
```

tgplay:

1. Scans those folders (no network, no Telegram login)
2. Reads the sidecar `.meta` file for expected vs downloaded size
3. Sniffs the file header (`ffprobe` when available)
4. Asks you to confirm the file and pick a player
5. Launches VLC (or IINA / mpv) against the `_partial` file

Telegram often writes chunks out of order. **tgplay does not remux the file.**

- **Matroska (`.mkv`)** is usually playable once the header is on disk
- **MP4** with a `moov` atom at the end may not start until the download finishes
- If the start of the file is still empty, the row is marked **not yet**

Original Telegram filenames are not in the cache path. Rows are labeled from the container, codec, and resolution instead.

## Privacy

tgplay never uploads your media. It only reads local Telegram cache files and starts a local player.

## Project docs

| File | Purpose |
| ---- | ------- |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development and PR guidelines |
| [LICENSE](LICENSE) | MIT license |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting |

## License

MIT — see [LICENSE](LICENSE).
