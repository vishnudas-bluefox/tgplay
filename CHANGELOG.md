# Changelog

## Unreleased

- Confirm the selected file before playback
- Ask which player to use; VLC is first and recommended
- Detect `/Applications/VLC.app` even when `vlc` is not on PATH
- Public GitHub repository and CI
- Homebrew tap formula: `brew install vishnudas-bluefox/tap/tgplay`

## 0.1.0 — 2026-08-13

- Initial CLI: scan Telegram for macOS `postbox/media` folders
- Parse `_partial.meta` for expected vs downloaded size
- Interactive curses UI with ↑/↓ selection and Enter to play
- `--list` mode for non-interactive output
- Launch mpv or IINA against in-progress files
- Default view hides stale leftover `_partial` files; `--all` shows everything
