"""Tests for the CKAN-free formatting helpers."""

from datetime import timezone

import pytest

from ckanext.unfold import formatting


def test_printable_file_size():
    assert formatting.printable_file_size(0) == "0 B"
    assert formatting.printable_file_size(-5) == "0 B"
    assert formatting.printable_file_size(1536) == "1.5 KB"
    assert formatting.printable_file_size(52428800) == "50.0 MB"
    assert formatting.printable_file_size(1024**6) == "1024.0 PB"  # clamped unit


def test_datetime_from_dos_valid_tuple():
    value = formatting.datetime_from_dos((2022, 11, 10, 0, 45, 10))

    assert value is not None
    assert (value.year, value.month, value.day) == (2022, 11, 10)
    assert value.tzinfo is timezone.utc
    assert value.strftime("%d/%m/%Y - %H:%M") == "10/11/2022 - 00:45"


def test_datetime_from_dos_zeroed_timestamp_is_skipped():
    """zipfile decodes a zero DOS date as (1980, 0, 0, ...)."""
    assert formatting.datetime_from_dos((1980, 0, 0, 0, 0, 0)) is None
    assert formatting.datetime_from_dos(None) is None
    assert formatting.datetime_from_dos(()) is None


def test_datetime_from_timestamp():
    value = formatting.datetime_from_timestamp(0)

    assert value is not None
    assert value.strftime("%d/%m/%Y - %H:%M") == "01/01/1970 - 00:00"
    assert formatting.datetime_from_timestamp(None) is None
    assert formatting.datetime_from_timestamp(10**20) is None


@pytest.mark.parametrize(
    ("fmt", "icon"),
    [
        ("png", "fa fa-file-image"),
        (".PNG", "fa fa-file-image"),
        ("tar", "fa fa-file-archive"),
        ("csv", "fa fa-file-csv"),
        ("md", formatting.DEFAULT_ICON),
        ("", formatting.DEFAULT_ICON),
    ],
)
def test_get_icon_by_format(fmt: str, icon: str):
    assert formatting.get_icon_by_format(fmt) == icon


@pytest.mark.parametrize(
    ("fmt", "icon"),
    [
        ("png", "fa fa-file-image format-png"),
        (".PNG", "fa fa-file-image format-png"),
        ("csv", "fa fa-file-csv format-csv"),
        # unknown extension: falls back to the default icon, keeps its class
        # (a theme may still style `.format-md` even without a dedicated
        # font-awesome icon for it)
        ("md", f"{formatting.DEFAULT_ICON} format-md"),
        # no extension at all: nothing to key a format class on
        ("", formatting.DEFAULT_ICON),
    ],
)
def test_file_icon(fmt: str, icon: str):
    assert formatting.file_icon(fmt) == icon


def test_name_and_format_from_path():
    assert formatting.name_from_path("a/b/c.txt") == "c.txt"
    assert formatting.name_from_path("a/b/") == "b"
    assert formatting.name_from_path("") == ""
    assert formatting.name_from_path(None) == ""
    assert formatting.get_format_from_name("c.txt") == ".txt"
    assert formatting.get_format_from_name("Makefile") == ""
