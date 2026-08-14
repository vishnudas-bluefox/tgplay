from pathlib import Path

from tgplay.media import sniff_header
from tgplay.player import (
    PLAYERS,
    build_play_command,
    default_player_index,
    list_installed_players,
)


def test_sniff_matroska():
    head = b"\x1aE\xdf\xa3" + b"\x00" * 20
    result = sniff_header(head)
    assert result.container == "matroska"
    assert result.media_kind == "video"
    assert result.playable is True


def test_sniff_mp4():
    head = b"\x00\x00\x00\x20ftypisom" + b"\x00" * 8
    result = sniff_header(head)
    assert result.container == "mp4"
    assert result.playable is True


def test_sniff_empty_not_playable():
    result = sniff_header(b"\x00" * 32)
    assert result.playable is False
    assert result.media_kind == "unknown"


def test_build_mpv_command():
    cmd = build_play_command(Path("/tmp/a_partial"), "mpv", "/usr/bin/mpv")
    assert cmd[0] == "/usr/bin/mpv"
    assert "--force-seekable=yes" in cmd
    assert cmd[-1] == "/tmp/a_partial"


def test_build_iina_command():
    cmd = build_play_command(Path("/tmp/a_partial"), "iina", "/opt/homebrew/bin/iina")
    assert cmd[0] == "/opt/homebrew/bin/iina"
    assert any(part.startswith("--mpv-") or part == "/tmp/a_partial" for part in cmd)
    assert cmd[-1] == "/tmp/a_partial"


def test_default_player_order_puts_vlc_first():
    assert PLAYERS[0] == "vlc"


def test_build_vlc_command_uses_macos_open():
    cmd = build_play_command(
        Path("/tmp/a_partial"),
        "vlc",
        "/Applications/VLC.app/Contents/MacOS/VLC",
    )
    assert cmd[:3] == ["open", "-a", "VLC"]
    assert cmd[-1] == "/tmp/a_partial"


def test_default_player_index_prefers_vlc():
    players = [("iina", "/iina"), ("vlc", "/vlc"), ("mpv", "/mpv")]
    assert default_player_index(players, preferred="auto") == 1
    assert default_player_index(players, preferred="vlc") == 1
    assert default_player_index(players, preferred="mpv") == 2


def test_list_installed_players_includes_vlc_app(monkeypatch, tmp_path: Path):
    vlc = tmp_path / "VLC.app" / "Contents" / "MacOS" / "VLC"
    vlc.parent.mkdir(parents=True)
    vlc.write_text("x")
    monkeypatch.setattr("tgplay.player.shutil.which", lambda name: None)
    monkeypatch.setattr(
        "tgplay.player.PLAYER_APPS",
        {"vlc": vlc, "iina": tmp_path / "missing", "mpv": tmp_path / "missing"},
    )
    found = list_installed_players()
    assert found[0][0] == "vlc"
    assert found[0][1] == str(vlc)
