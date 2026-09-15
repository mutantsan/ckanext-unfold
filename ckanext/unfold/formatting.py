"""Pure formatting helpers with no CKAN dependency."""

from __future__ import annotations

import math
import pathlib
from collections.abc import Sequence
from datetime import datetime, timezone


SIZE_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")
DEFAULT_DATE_FORMAT = "%d/%m/%Y - %H:%M"
DEFAULT_ICON = "fa fa-file"

GROUPED_ICONS = {
    ("csv",): "fa fa-file-csv",
    ("txt", "tsv", "ini", "nfo", "log"): "fa fa-file-text",
    ("xls", "xlsx"): "fa fa-file-excel",
    ("doc", "docx"): "fa fa-file-word",
    ("ppt", "pptx", "pptm"): "fa fa-file-powerpoint",
    (
        "ai",
        "gif",
        "ico",
        "tif",
        "tiff",
        "webp",
        "png",
        "jpeg",
        "jpg",
        "svg",
        "bmp",
        "psd",
    ): "fa fa-file-image",
    (
        "7z",
        "rar",
        "zip",
        "zipx",
        "gzip",
        "gz",
        "bz2",
        "xz",
        "tgz",
        "tar",
        "deb",
        "cbr",
        "pkg",
        "apk",
    ): "fa fa-file-archive",
    ("pdf",): "fa fa-file-pdf",
    (
        "json",
        "xhtml",
        "py",
        "css",
        "rs",
        "html",
        "php",
        "sql",
        "java",
        "class",
    ): "fa fa-file-code",
    ("xml", "dtd"): "fa fa-file-contract",
    ("mp3", "wav", "wma", "aac", "flac", "mpa", "ogg"): "fa fa-file-audio",
    ("fnt", "fon", "otf", "ttf"): "fa fa-font",
    ("pub", "pem"): "fa fa-file-shield",
}

ICON_BY_FORMAT = {
    fmt: icon for formats, icon in GROUPED_ICONS.items() for fmt in formats
}


def get_icon_by_format(fmt: str) -> str:
    return ICON_BY_FORMAT.get(fmt.lstrip(".").lower(), DEFAULT_ICON)


def file_icon(fmt: str) -> str:
    """Icon classes for a file node: the base font-awesome icon plus a
    ``format-<ext>`` class, e.g. ``"fa fa-file-csv format-csv"``.

    Folders never call this (they use a plain ``fa fa-folder``, matched by
    its own selector); every entry's file branch should.
    """
    fmt_clean = fmt.lstrip(".").lower()
    icon = ICON_BY_FORMAT.get(fmt_clean, DEFAULT_ICON)

    return f"{icon} format-{fmt_clean}" if fmt_clean else icon


def name_from_path(path: str | None) -> str:
    return path.rstrip("/").split("/")[-1] if path else ""


def get_format_from_name(name: str) -> str:
    return pathlib.Path(name).suffix


def printable_file_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "0 B"

    i = min(int(math.log(size_bytes, 1024)), len(SIZE_UNITS) - 1)
    s = round(size_bytes / math.pow(1024, i), 1)

    return f"{s} {SIZE_UNITS[i]}"


def datetime_from_dos(parts: Sequence[int] | None) -> datetime | None:
    """Build a datetime from a ZIP/RAR ``date_time`` tuple.

    Archives written with a zeroed DOS timestamp decode to
    ``(1980, 0, 0, 0, 0, 0)``, which ``datetime`` rejects; such entries
    get no date instead of failing the whole listing. The archive gives
    no zone, so UTC is attached purely to keep the value unambiguous.
    """
    if not parts:
        return None

    try:
        return datetime(*parts[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def datetime_from_timestamp(timestamp: float | None) -> datetime | None:
    """Build a UTC datetime from a POSIX timestamp, ``None`` if it is invalid."""
    if timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None
