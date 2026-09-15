from __future__ import annotations

import logging
from io import BytesIO

import rarfile
from rarfile import Error as RarError
from rarfile import RarInfo

import ckanext.unfold.exception as unf_exception
import ckanext.unfold.types as unf_types
from ckanext.unfold.adapters.base import BaseAdapter
from ckanext.unfold.formatting import datetime_from_dos

log = logging.getLogger(__name__)


class RarAdapter(BaseAdapter):
    open_errors = (RarError,)

    def iter_entries(self) -> list[unf_types.Entry]:
        """List a RAR archive's entries.

        RAR doesn't allow us to download it partially and fetch only the
        file list.
        """
        content = self.get_file_content()
        archive = rarfile.RarFile(BytesIO(content))

        needs_password = archive.needs_password()

        if needs_password and not self.resource_view.get("archive_pass"):
            raise unf_exception.UnfoldError("Error. Archive is protected with password")

        if needs_password:
            archive.setpassword(self.resource_view["archive_pass"])

        file_list = archive.infolist()

        if not file_list:
            raise unf_exception.UnfoldError(
                "Error. The archive is either empty or the password is incorrect."
            )

        return [self._to_entry(info) for info in file_list]

    @staticmethod
    def _to_entry(entry: RarInfo) -> unf_types.Entry:
        mtime = entry.mtime

        if mtime is None and isinstance(entry.date_time, tuple):
            mtime = datetime_from_dos(entry.date_time)

        return unf_types.Entry(
            path=(entry.filename or "").rstrip("/"),
            is_dir=entry.isdir(),
            size=entry.compress_size,
            mtime=mtime,
        )
