# Contributing

Thanks for your interest in improving tgplay.

## Development setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/vishnudas-bluefox/tgplay.git
cd tgplay
uv sync --extra dev
```

Run the CLI:

```bash
uv run tgplay
uv run tgplay --list
uv run python tgplay.py
```

Run tests:

```bash
uv run pytest
```

## Making changes

1. Create a branch from `main`.
2. Keep changes focused and minimal.
3. Update `CHANGELOG.md` under **Unreleased** for user-visible changes.
4. Add or update tests for scanner, meta parsing, and player command construction.

## Pull requests

- Describe what changed and why.
- Ensure `uv run pytest` and `uv run tgplay --list` succeed.

## Reporting issues

Include:

- macOS version and Python version (`uv run python --version`)
- Whether you use Telegram from the App Store or telegram.org
- Full command or steps to reproduce
- Error output (redact personal paths if needed)

See [SECURITY.md](SECURITY.md) for reporting security issues.
