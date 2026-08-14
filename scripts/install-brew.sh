#!/usr/bin/env bash
set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install from https://brew.sh"
  exit 1
fi

brew tap vishnudas-bluefox/tap
if brew trust --help >/dev/null 2>&1; then
  brew trust vishnudas-bluefox/tap || true
fi
brew install tgplay

echo ""
echo "Installed tgplay"
echo "Try: tgplay --version"
echo "Then: tgplay"
