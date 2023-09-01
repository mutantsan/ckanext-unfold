from __future__ import annotations

import logging
from typing import Any
from zipfile import BadZipFile, LargeZipFile, ZipFile, ZipInfo
from datetime import datetime as dt

import ckan.plugins.toolkit as tk

import ckanext.unfold.types as unf_types
import ckanext.unfold.utils as unf_utils

log = logging.getLogger(__name__)


def build_directory_tree(filepath: str) -> list[unf_types.Node]:
    try:
        with ZipFile(filepath) as archive:
            file_list: list[ZipInfo] = archive.infolist()
    except (LargeZipFile, BadZipFile) as e:
        log.error(f"Error openning zip archive: {e}")
        return []

    nodes: list[unf_types.Node] = []

    for entry in file_list:
        nodes.append(_build_node(entry))

    return nodes


def _build_node(entry: ZipInfo) -> unf_types.Node:
    parts = [p for p in entry.filename.split("/") if p]
    name = unf_utils.name_from_path(entry.filename)
    fmt = "folder" if entry.is_dir() else unf_utils.get_format_from_name(name)

    return unf_types.Node(
        id=entry.filename or "",
        text=unf_utils.name_from_path(entry.filename),
        icon="fa fa-folder" if entry.is_dir() else unf_utils.get_icon_by_format(fmt),
        state={"opened": True},
        parent="/".join(parts[:-1]) + "/" if parts[:-1] else "#",
        data=_prepare_table_data(entry),
    )


def _prepare_table_data(entry: ZipInfo) -> dict[str, Any]:
    name = unf_utils.name_from_path(entry.filename)
    fmt = "" if entry.is_dir() else unf_utils.get_format_from_name(name)
    modified_at = tk.h.render_datetime(dt(*entry.date_time), date_format="%d/%m/%Y - %H:%M")

    return {
        "size": unf_utils.printable_file_size(entry.compress_size)
        if entry.compress_size
        else "",
        "type": "folder" if entry.is_dir() else "file",
        "format": fmt,
        "modified_at": modified_at,
    }
