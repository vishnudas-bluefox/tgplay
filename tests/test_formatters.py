from tgplay.media import format_bytes, format_duration, parse_size, progress_bar


def test_format_bytes():
    assert format_bytes(0) == "0 B"
    assert format_bytes(512) == "512 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(2_040_000_000) == "1.90 GB"


def test_format_duration():
    assert format_duration(None) == ""
    assert format_duration(65) == "1m 05s"
    assert format_duration(7701) == "2h 08m"


def test_parse_size():
    assert parse_size("2048") == 2048
    assert parse_size("2K") == 2048
    assert parse_size("2MB") == 2 * 1024 * 1024
    assert parse_size("1.5G") == int(1.5 * 1024**3)


def test_progress_bar_bounds():
    assert progress_bar(None, 10) == "?" * 10
    assert progress_bar(0, 10) == "░" * 10
    assert progress_bar(1, 10) == "█" * 10
    assert "█" in progress_bar(0.42, 24)
    assert len(progress_bar(0.42, 24)) == 24
