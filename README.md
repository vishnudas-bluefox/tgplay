# tgplay — watch Telegram video while downloading on macOS

Play a Telegram video on your Mac **while it is still downloading**. You do not have to wait until Telegram finishes saving the file.

Telegram for Mac usually makes you wait until the whole video is saved. tgplay watches that download, shows progress, and opens it in VLC so you can watch while downloading.

Created by [Vishnudas-bluefox](https://github.com/vishnudas-bluefox)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](#1-install-homebrew-if-you-dont-have-it)

It stays on your Mac. No Telegram login. No upload.

---

## What you need

- A Mac
- [Telegram for Mac](https://macos.telegram.org/)
- [Homebrew](https://brew.sh) (the usual way to install Mac command-line tools)
- [VLC](https://www.videolan.org/vlc/) to play the video (recommended)

If you already have Homebrew and VLC, skip to [Install tgplay](#2-install-tgplay).

---

## 1. Install Homebrew (if you don’t have it)

1. Open **Terminal** (Spotlight: press `Cmd + Space`, type `Terminal`, press Return).
2. Paste this line and press Return:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

3. Follow the on-screen prompts.
4. If it asks you to run two more commands at the end (“Next steps”), copy those too, then press Return after each one.

Check that it worked:

```bash
brew --version
```

You should see a version number, not “command not found”.

---

## 2. Install tgplay

In Terminal, paste:

```bash
brew install vishnudas-bluefox/tap/tgplay
```

That one line downloads tgplay and makes the `tgplay` command available in every Terminal window.

If Homebrew says the tap is not trusted, run these three lines instead:

```bash
brew tap vishnudas-bluefox/tap
brew trust --formula vishnudas-bluefox/tap/tgplay
brew install tgplay
```

Check that it worked:

```bash
tgplay --version
```

You should see `tgplay 0.1.0` (or a later version).

Later, to update:

```bash
brew upgrade tgplay
```

---

## 3. Install VLC (if you don’t have it)

VLC is the player tgplay recommends.

```bash
brew install --cask vlc
```

Or download it from [videolan.org](https://www.videolan.org/vlc/).

IINA and mpv also work if they are already installed. You pick the player each time, before anything starts.

---

## 4. Use it

1. Open **Telegram** and start downloading a video or a large file.
2. Open **Terminal**.
3. Type `tgplay` and press Return.

```bash
tgplay
```

4. A list of Telegram downloads appears. The highlighted row is the one with `❯`.
5. Use the **up / down arrow keys** to highlight the file you want.
6. Press **Return**. A confirm screen shows the file and a list of players.
7. Leave **VLC** selected (it is first), or use the arrows to pick another player.
8. Press **Return** again. VLC opens that file.
9. Press **`q`** in Terminal when you are done, to quit tgplay.

Nothing plays until you confirm both the file and the player.

```
 Telegram Downloads

 ❯ 🎬 H264 · 1280×536          33 MB / 1.41 GB   2%
      downloading · playable

   🎬 HEVC · 1620×1080         2.93 GB / 2.93 GB  100%
      complete

 ↑↓ choose a file     Return confirm     q quit
```

---

## Keys

While the file list is open:

| Key | What it does |
| --- | --- |
| `↑` / `↓` | Move to another file |
| `Return` or Space | Confirm this file, then pick a player |
| `o` | Show the file in Finder |
| `d` | Open your Downloads folder |
| `r` | Refresh the list |
| `q` | Quit |

On the confirm / player screen:

| Key | What it does |
| --- | --- |
| `↑` / `↓` | Choose VLC, IINA, or mpv |
| `Return` | Start that player |
| `Esc` or `n` | Go back — nothing starts |

---

## If something goes wrong

**`brew: command not found`**  
Homebrew is not installed, or Terminal cannot see it. Do [step 1](#1-install-homebrew-if-you-dont-have-it) again, including any “Next steps” commands Homebrew printed.

**`tgplay: command not found`**  
It is not installed, or you need a new Terminal window. Run the install line in [step 2](#2-install-tgplay), close Terminal, open it again, then type `tgplay`.

**The list is empty**  
Start the download in Telegram first, then run `tgplay`. Small photos and stickers are hidden on purpose. Very old leftover files are hidden unless you run `tgplay --all`.

**It says “not yet” or VLC will not play**  
Telegram sometimes writes the file in pieces. MKV videos usually play early. Some MP4 files only play after the download is finished. Wait a bit, press `r` to refresh, and try again.

**Homebrew asks you to trust the tap**  
That is normal for a tool that is not in the official Homebrew catalog. Use the three-line install in [step 2](#2-install-tgplay).

**The name looks like `#431659` instead of the movie title**  
Telegram does not store the original filename in that cache folder. tgplay shows the video type, size, and progress instead.

---

## Common questions

**Can I watch a Telegram video on Mac while it is downloading?**  
Yes. That is what tgplay is for. Start the download in Telegram for Mac, run `tgplay` in Terminal, pick the file, and open it in VLC.

**Is there a Telegram “watch while downloading” tool for macOS?**  
Telegram’s Mac app does not give you a simple way to play a large file mid-download. tgplay is a free, local command-line tool that finds the in-progress file and plays it.

**Does this work with Telegram Desktop or only Telegram for Mac?**  
It is built for the official Telegram for Mac app (the one from telegram.org / the Mac App Store).

**Do I need to log in or give tgplay my Telegram account?**  
No. It only reads the download files already on your Mac.

## Privacy

tgplay never sends your videos anywhere. It only looks at Telegram’s download folder on this Mac and opens a player you already have.

---

## Extra commands (optional)

Most people only need `tgplay`. These are extras:

```bash
tgplay --list          # print the list and quit (no arrows)
tgplay --all           # also show older leftover files
tgplay --player vlc    # pre-select VLC on the confirm screen
```

---

## For developers

Install from source:

```bash
git clone https://github.com/vishnudas-bluefox/tgplay.git
cd tgplay
uv sync
uv run tgplay
```

How it finds files, the Homebrew formula, and the cache path are documented in [packaging/README.md](packaging/README.md).

| File | Purpose |
| --- | --- |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to send a change |
| [LICENSE](LICENSE) | MIT license |
| [SECURITY.md](SECURITY.md) | How to report a security issue |

## License

MIT — see [LICENSE](LICENSE).
