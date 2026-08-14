from pathlib import Path

from tgplay.scanner import parse_partial_meta, scan_media_dir
from tgplay.telegram import parse_resource_name


def test_parse_resource_name():
    info = parse_resource_name("telegram-cloud-document-4-5940272338275670460_partial")
    assert info is not None
    assert info.kind == "document"
    assert info.dc_id == 4
    assert info.resource_id == "5940272338275670460"
    assert info.is_partial is True

    done = parse_resource_name("telegram-cloud-document-4-5940272338275670460")
    assert done is not None and done.is_partial is False

    assert parse_resource_name("telegram-peer-photo-size-5-1-0-0-0") is None
    assert parse_resource_name("telegram-cloud-document-4-1_partial.meta") is None


def test_parse_partial_meta_complete():
    # 36-byte complete: expected == downloaded == 1964
    data = bytes.fromhex(
        "8714ac7b323759e501000000ac070000000000000000000000000000ac07000000000000"
    )
    meta = parse_partial_meta(data)
    assert meta.expected_size == 1964
    assert meta.downloaded_size == 1964


def test_parse_partial_meta_in_progress():
    # offset 12 = expected 3145560793, offset 28 = downloaded 2888171520
    data = bytes.fromhex(
        "8714ac7ba51b2ace01000000d9927dbb000000000000000000000000000026ac00000000"
        "000024ac000000000000020000000000000050ab0000000000000800000000000000c0a9"
        "000000000000080000000000"
    )
    meta = parse_partial_meta(data)
    assert meta.expected_size == 3_145_568_985
    assert meta.downloaded_size == 2_888_171_520


def test_parse_partial_meta_unknown():
    data = bytes.fromhex("8714ac7b1cdf442100000000ffffffffffffffff")
    meta = parse_partial_meta(data)
    assert meta.expected_size is None
    assert meta.downloaded_size is None


def test_scan_groups_hardlinked_partial_and_complete(tmp_path: Path):
    media = tmp_path / "postbox" / "media"
    media.mkdir(parents=True)
    payload = b"\x1aE\xdf\xa3" + b"matroska-like" + b"\x00" * 200
    complete = media / "telegram-cloud-document-4-111"
    complete.write_bytes(payload)
    partial = media / "telegram-cloud-document-4-111_partial"
    partial.hardlink_to(complete)
    meta = (
        bytes.fromhex("8714ac7b323759e501000000")
        + int(len(payload)).to_bytes(8, "little")
        + b"\x00" * 8
        + int(len(payload)).to_bytes(8, "little")
    )
    (media / "telegram-cloud-document-4-111_partial.meta").write_bytes(meta)

    items = scan_media_dir(media, min_size=0)
    assert len(items) == 1
    assert items[0].is_complete is True
    assert items[0].size == len(payload)
    assert items[0].expected_size == len(payload)


def test_scan_keeps_incomplete_partial(tmp_path: Path):
    media = tmp_path / "media"
    media.mkdir()
    data = b"\x1aE\xdf\xa3" + b"x" * 500
    path = media / "telegram-cloud-document-4-222_partial"
    path.write_bytes(data)
    expected, downloaded = 10_000, len(data)
    meta = (
        bytes.fromhex("8714ac7ba51b2ace01000000")
        + expected.to_bytes(8, "little")
        + b"\x00" * 8
        + downloaded.to_bytes(8, "little")
    )
    path.with_name(path.name + ".meta").write_bytes(meta)

    items = scan_media_dir(media, min_size=4096)
    assert len(items) == 1
    assert items[0].is_complete is False
    assert items[0].expected_size == 10_000
    assert items[0].downloaded == downloaded


def test_select_items_prefers_active_and_recent(tmp_path: Path):
    from tgplay.scanner import MediaItem, select_items

    now = 1_000_000.0
    active = MediaItem(
        path=tmp_path / "a_partial",
        resource_id="1",
        dc_id=4,
        account="stable/account-1",
        is_partial=True,
        is_complete=False,
        size=100,
        downloaded=100,
        expected_size=1000,
        mtime=now - 60,
    )
    stale = MediaItem(
        path=tmp_path / "b_partial",
        resource_id="2",
        dc_id=4,
        account="appstore/account-1",
        is_partial=True,
        is_complete=False,
        size=50,
        downloaded=50,
        expected_size=5000,
        mtime=now - 10 * 24 * 3600,
    )
    recent = MediaItem(
        path=tmp_path / "c",
        resource_id="3",
        dc_id=4,
        account="stable/account-1",
        is_partial=False,
        is_complete=True,
        size=2000,
        downloaded=2000,
        expected_size=2000,
        mtime=now - 120,
    )
    chosen = select_items([stale, recent, active], now=now)
    assert [item.resource_id for item in chosen] == ["1", "3"]
