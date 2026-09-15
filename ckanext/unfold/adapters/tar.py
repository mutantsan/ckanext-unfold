from __future__ import annotations

import logging
from io import BytesIO
from tarfile import TarError, TarInfo
from tarfile import open as tar_open
from typing import Literal

import ckanext.unfold.types as unf_types
from ckanext.unfold.adapters.base import BaseAdapter
from ckanext.unfold.formatting import datetime_from_timestamp

log = logging.getLogger(__name__)


class TarAdapter(BaseAdapter):
    mode: Literal["r", "r:gz", "r:xz", "r:bz2"] = "r"
    open_errors = (TarError,)

    def iter_entries(self) -> list[unf_types.Entry]:
        """List a tar archive's entries.

        Tar doesn't allow us to download it partially and fetch only the
        file list, because the information about each file is stored
        alongside its data rather than in one central index.
        """
        content = self.get_file_content()

        return [
            self._to_entry(m)
            for m in tar_open(fileobj=BytesIO(content), mode=self.mode).getmembers()
        ]

    @staticmethod
    def _to_entry(entry: TarInfo) -> unf_types.Entry:
        return unf_types.Entry(
            path=entry.name.rstrip("/"),
            is_dir=entry.isdir(),
            size=entry.size,
            mtime=datetime_from_timestamp(entry.mtime),
        )


class TarGzAdapter(TarAdapter):
    mode = "r:gz"


class TarXzAdapter(TarAdapter):
    mode = "r:xz"


class TarBz2Adapter(TarAdapter):
    mode = "r:bz2"
