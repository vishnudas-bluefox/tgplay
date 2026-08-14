from pathlib import Path

from tgplay.telegram import discover_media_dirs, telegram_roots


def test_telegram_roots_and_media_dirs(tmp_path: Path):
    bundle = tmp_path / "Library/Group Containers/6N38VWS5BX.ru.keepcoder.Telegram"
    media = bundle / "stable/account-123/postbox/media"
    media.mkdir(parents=True)
    (media / "telegram-cloud-document-4-1").write_bytes(b"x")

    roots = telegram_roots(home=tmp_path)
    assert bundle in roots
    dirs = discover_media_dirs(roots)
    assert media in dirs
