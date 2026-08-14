from pathlib import Path

from tgplay.scanner import MediaItem
from tgplay.monitor import TrackedItem
from tgplay.ui import App


def _item(tmp_path: Path) -> MediaItem:
    path = tmp_path / "telegram-cloud-document-4-1_partial"
    path.write_bytes(b"\x1aE\xdf\xa3")
    return MediaItem(
        path=path,
        resource_id="1",
        dc_id=4,
        account="stable/account-1",
        is_partial=True,
        is_complete=False,
        size=100,
        downloaded=100,
        expected_size=1000,
        mtime=0.0,
        media_kind="video",
        playable=True,
    )


def test_enter_opens_confirm_prompt_instead_of_playing(tmp_path: Path, monkeypatch):
    app = App([tmp_path], min_size=0, player="auto")
    item = _item(tmp_path)
    app.rows = [TrackedItem(item=item, speed_bps=0.0)]
    monkeypatch.setattr(
        "tgplay.ui.list_installed_players",
        lambda: [("vlc", "/Applications/VLC.app/Contents/MacOS/VLC"), ("iina", "/iina")],
    )
    launched: list[tuple] = []
    monkeypatch.setattr("tgplay.ui.play", lambda *args, **kwargs: launched.append((args, kwargs)) or (True, "launched"))

    app.open_play_prompt()
    assert app.prompt is not None
    assert app.prompt.item.path == item.path
    assert app.prompt.players[app.prompt.player_index][0] == "vlc"
    assert launched == []

    app.move_prompt_player(1)
    assert app.prompt.players[app.prompt.player_index][0] == "iina"
    app.confirm_play()
    assert app.prompt is None
    assert launched[0][1]["preferred"] == "iina"


def test_cancel_prompt_does_not_play(tmp_path: Path, monkeypatch):
    app = App([tmp_path], min_size=0, player="auto")
    app.rows = [TrackedItem(item=_item(tmp_path), speed_bps=0.0)]
    monkeypatch.setattr("tgplay.ui.list_installed_players", lambda: [("vlc", "/vlc")])
    launched: list[object] = []
    monkeypatch.setattr("tgplay.ui.play", lambda *args, **kwargs: launched.append(1) or (True, "x"))
    app.open_play_prompt()
    app.cancel_prompt()
    assert app.prompt is None
    assert launched == []
    assert "cancel" in app.message.lower()
