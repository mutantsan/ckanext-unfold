from __future__ import annotations

import logging
from io import BytesIO

from ar import Archive, ArchiveError
from ar.archive import ArPath

import ckanext.unfold.types as unf_types
from ckanext.unfold.adapters.base import BaseAdapter

log = logging.getLogger(__name__)


class ArAdapter(BaseAdapter):
    open_errors = (ArchiveError,)

    def iter_entries(self) -> list[unf_types.Entry]:
        """List an ar archive's entries. ar archives have no directories."""
        content = self.get_file_content()
        archive = Archive(BytesIO(content))

        return [self._to_entry(e) for e in archive.entries]

    @staticmethod
    def _to_entry(entry: ArPath) -> unf_types.Entry:
        return unf_types.Entry(
            path=entry.name.rstrip("/"), is_dir=False, size=entry.size
        )
