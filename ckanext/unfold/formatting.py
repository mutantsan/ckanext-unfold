"""Pure formatting helpers with no CKAN dependency."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime

SIZE_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")


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
        return datetime(*parts[:6], tzinfo=UTC)
    except (TypeError, ValueError, OverflowError):
        return None


def datetime_from_timestamp(timestamp: float | None) -> datetime | None:
    """Build a UTC datetime from a POSIX timestamp, ``None`` if it is invalid."""
    if timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(timestamp, tz=UTC)
    except (TypeError, ValueError, OverflowError, OSError):
        return None
