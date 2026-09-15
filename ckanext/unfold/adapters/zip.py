from __future__ import annotations

import logging
from io import BytesIO
from typing import Any
from zipfile import ZIP_STORED, BadZipFile, LargeZipFile, ZipFile, ZipInfo

import ckan.plugins.toolkit as tk

import ckanext.unfold.config as unf_config
import ckanext.unfold.exception as unf_exception
import ckanext.unfold.types as unf_types
import ckanext.unfold.utils as unf_utils
from ckanext.unfold.adapters import remote
from ckanext.unfold.adapters.base import DEFAULT_TIMEOUT, BaseAdapter
from ckanext.unfold.formatting import datetime_from_dos

log = logging.getLogger(__name__)


class ZipAdapter(BaseAdapter):
    # Remote archives are opened through a Range-backed reader; only the
    # central directory is transferred, so the resource's declared size is
    # not a reason to refuse the preview.
    partial_read = True

    def get_node_list(self) -> list[unf_types.Node]:
        try:
            if self.is_upload:
                file_list = ZipFile(BytesIO(self.get_file_content())).infolist()
            else:
                file_list = self.get_file_list_from_url(self.filepath)
        except (LargeZipFile, BadZipFile) as e:
            raise unf_exception.UnfoldError(f"Error opening archive: {e}") from e

        return [self._build_node(entry) for entry in self.ensure_dir_entries(file_list)]

    def get_file_list_from_url(self, url: str) -> list[ZipInfo]:
        """Read the ZIP central directory from a remote URL.

        The archive is opened through a seekable, Range-backed file object,
        so ``zipfile`` fetches only the end-of-central-directory records and
        the central directory itself, wherever they sit in the file. This
        also covers ZIP64 archives (over 4 GiB or 65,535 entries): their
        locator stores absolute offsets, which is why a truncated tail can
        never be parsed on its own. The configured size limit applies to the
        bytes transferred, not to the archive size.

        Servers that ignore ``Range`` return the whole file, which is
        accepted only within the limit.
        """
        fp = remote.open_remote(url, unf_config.get_max_file_size(), DEFAULT_TIMEOUT)

        with fp, ZipFile(fp) as archive:
            return archive.infolist()

    def _build_node(self, entry: ZipInfo) -> unf_types.Node:
        parts = [p for p in entry.filename.split("/") if p]
        name = unf_utils.name_from_path(entry.filename)
        fmt = "folder" if entry.is_dir() else unf_utils.get_format_from_name(name)

        return unf_types.Node(
            id=entry.filename.rstrip("/") or "",
            text=unf_utils.name_from_path(entry.filename),
            icon="fa fa-folder" if entry.is_dir() else unf_utils.file_icon(fmt),
            state={"opened": True},
            parent="/".join(parts[:-1]) if parts[:-1] else "#",
            data=self._prepare_table_data(entry),
        )

    def _prepare_table_data(self, entry: ZipInfo) -> dict[str, Any]:
        return {
            "size": (
                unf_utils.printable_file_size(entry.compress_size)
                if entry.compress_size
                else ""
            ),
            "modified_at": tk.h.render_datetime(
                datetime_from_dos(entry.date_time),
                date_format=unf_utils.DEFAULT_DATE_FORMAT,
            )
            or "",
        }

    def ensure_dir_entries(self, file_list: list[ZipInfo]) -> list[ZipInfo]:
        """Ensure directory entries exist in a ZipFile infolist.

        ZIP archives may omit explicit directory entries ("dir/") and only
        contain file paths ("dir/file.txt"). Infolist() then misses those
        directories. This function infers and adds the missing ZipInfo
        entries so consumers can rely on a complete directory tree.
        """
        names = [zi.filename for zi in file_list]
        name_set = set(names)

        inferred_dirs = set()
        for name in names:
            # treat "dir/" as a dir and "dir/file" as a file
            s = name.removesuffix("/")
            i = s.rfind("/")
            while i != -1:
                d = s[: i + 1]  # keep trailing slash to mark as dir
                if d not in name_set:
                    inferred_dirs.add(d)
                i = s.rfind("/", 0, i)

        if inferred_dirs:
            for d in inferred_dirs:
                zi = ZipInfo(d)
                # Mark as a directory: set Unix mode drwxr-xr-x
                zi.external_attr = 0o40755 << 16
                zi.compress_type = ZIP_STORED
                zi.file_size = 0
                file_list.append(zi)

        return file_list
