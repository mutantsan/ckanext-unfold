from __future__ import annotations

import logging
import tarfile
from datetime import datetime as dt
from tarfile import TarError, TarInfo
from typing import Any, Optional

import ckan.plugins.toolkit as tk

import ckanext.unfold.types as unf_types
import ckanext.unfold.utils as unf_utils

log = logging.getLogger(__name__)


def build_directory_tree(filepath: str, compression: Optional[str] = None):
    mode = "r" if not compression else f"r:{compression}"

    try:
        with tarfile.open(filepath, mode) as archive:
            file_list: list[TarInfo] = archive.getmembers()
    except TarError as e:
        log.error(f"Error openning rar archive: {e}")
        return []

    nodes: list[unf_types.Node] = []

    for entry in file_list:
        nodes.append(_build_node(entry))

    return nodes


def _build_node(entry: TarInfo) -> unf_types.Node:
    parts = [p for p in entry.name.split("/") if p]
    name = unf_utils.name_from_path(entry.name)
    fmt = "folder" if entry.isdir() else unf_utils.get_format_from_name(name)

    return unf_types.Node(
        id=entry.name or "",
        text=unf_utils.name_from_path(entry.name),
        icon="fa fa-folder" if entry.isdir() else unf_utils.get_icon_by_format(fmt),
        state={"opened": True},
        parent="/".join(parts[:-1]) if parts[:-1] else "#",
        data=_prepare_table_data(entry),
    )


def _prepare_table_data(entry: TarInfo) -> dict[str, Any]:
    name = unf_utils.name_from_path(entry.name)
    fmt = "" if entry.isdir() else unf_utils.get_format_from_name(name)
    modified_at = tk.h.render_datetime(dt.fromtimestamp(entry.mtime), with_hours=True)

    return {
        "size": unf_utils.printable_file_size(entry.size) if entry.size else "",
        "type": "folder" if entry.isdir() else "file",
        "format": fmt,
        "modified_at": modified_at,
    }
