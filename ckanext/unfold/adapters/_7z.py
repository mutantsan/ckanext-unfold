from __future__ import annotations

import logging
from typing import Any, Optional
from io import BytesIO

import requests
import py7zr
from py7zr import FileInfo, exceptions

import ckan.plugins.toolkit as tk

import ckanext.unfold.types as unf_types
import ckanext.unfold.utils as unf_utils
import ckanext.unfold.exception as unf_exception

log = logging.getLogger(__name__)


def build_directory_tree(filepath: str, remote: Optional[bool] = False):
    try:
        if remote:
            file_list = get7zlist_from_url(filepath)
        else:
            with py7zr.SevenZipFile(filepath) as archive:
                if archive.needs_password():
                    raise unf_exception.UnfoldError(
                        f"Archive is protected with password"
                    )

                file_list: list[FileInfo] = archive.list()
    except exceptions.ArchiveError as e:
        log.error(f"Error openning 7z archive: {e}")
        return []

    nodes: list[unf_types.Node] = []

    for entry in file_list:
        nodes.append(_build_node(entry))

    return nodes


def _build_node(entry: FileInfo) -> unf_types.Node:
    parts = [p for p in entry.filename.split("/") if p]
    name = unf_utils.name_from_path(entry.filename)
    fmt = "folder" if entry.is_directory else unf_utils.get_format_from_name(name)

    return unf_types.Node(
        id=entry.filename or "",
        text=unf_utils.name_from_path(entry.filename),
        icon="fa fa-folder"
        if entry.is_directory
        else unf_utils.get_icon_by_format(fmt),
        state={"opened": True},
        parent="/".join(parts[:-1]) if parts[:-1] else "#",
        data=_prepare_table_data(entry),
    )


def _prepare_table_data(entry: FileInfo) -> dict[str, Any]:
    name = unf_utils.name_from_path(entry.filename)
    fmt = "" if entry.is_directory else unf_utils.get_format_from_name(name)
    modified_at = tk.h.render_datetime(entry.creationtime, with_hours=True)

    return {
        "size": unf_utils.printable_file_size(entry.compressed)
        if entry.compressed
        else "--",
        "type": "folder" if entry.is_directory else "file",
        "format": fmt,
        "modified_at": modified_at,
    }


def get7zlist_from_url(url) -> list[FileInfo]:
    """Download an archive and fetch a file list. Rar file doesn't allow us
    to download it partially and fetch only file list."""
    resp = requests.get(url)

    return py7zr.SevenZipFile(BytesIO(resp.content)).infolist()
