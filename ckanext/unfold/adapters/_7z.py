from __future__ import annotations

import logging
from typing import Any

import py7zr
from py7zr import FileInfo, exceptions

import ckan.plugins.toolkit as tk

import ckanext.unfold.types as unf_types
import ckanext.unfold.utils as unf_utils

log = logging.getLogger(__name__)


def build_directory_tree(filepath: str):
    try:
        with py7zr.SevenZipFile(filepath) as archive:
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
