# Packaging

How to publish **tgplay** so Mac users can install it with Homebrew.

## What users type

One command (taps automatically):

```bash
brew install vishnudas-bluefox/tap/tgplay
```

Or tap once, then it is just `brew install tgplay`:

```bash
brew tap vishnudas-bluefox/tap
brew install tgplay
```

After either path, `tgplay` is on their PATH from any terminal.

`brew install tgplay` with **no tap** only works after the formula is accepted into [homebrew-core](https://github.com/Homebrew/homebrew-core). That needs adoption and review. The personal tap is the supported install today.

## Release checklist

1. Bump `version` in `pyproject.toml` and `tgplay/__init__.py`.
2. Update `CHANGELOG.md`.
3. Commit and push `main`.
4. Tag and release:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   gh release create v0.1.0 --title "tgplay 0.1.0" --generate-notes
   ```

5. Checksum the source tarball:

   ```bash
   curl -sL https://github.com/vishnudas-bluefox/tgplay/archive/refs/tags/v0.1.0.tar.gz | shasum -a 256
   ```

6. Put that hash in:
   - `packaging/homebrew/tgplay.rb`
   - `vishnudas-bluefox/homebrew-tap` → `Formula/tgplay.rb`

7. Push the tap repo.

8. Smoke-test:

   ```bash
   brew update
   brew install --verbose vishnudas-bluefox/tap/tgplay
   tgplay --version
   ```
