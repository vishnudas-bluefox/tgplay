class Tgplay < Formula
  desc "Play Telegram for Mac downloads from the terminal while they are still arriving"
  homepage "https://github.com/vishnudas-bluefox/tgplay"
  url "https://github.com/vishnudas-bluefox/tgplay/archive/refs/tags/v0.1.0.tar.gz"
  version "0.1.0"
  sha256 "REPLACE_AFTER_TAG"
  license "MIT"
  head "https://github.com/vishnudas-bluefox/tgplay.git", branch: "main"

  depends_on "python@3.12"

  def install
    libexec.install "tgplay"
    (lib/"tgplay").install_symlink libexec
    (bin/"tgplay").install "bin/tgplay"
  end

  def caveats
    <<~EOS
      tgplay needs a video player. VLC is recommended:

        brew install --cask vlc

      Then run:

        tgplay
    EOS
  end

  test do
    assert_match "tgplay 0.1.0", shell_output("#{bin}/tgplay --version")
  end
end
