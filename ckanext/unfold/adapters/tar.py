from __future__ import annotations

import logging
import tarfile
from tarfile import TarError, TarInfo
from typing import Optional

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
        text=_get_node_text(entry),
        icon="fa fa-folder" if entry.isdir() else unf_utils.get_icon_by_format(fmt),
        state={"opened": True},
        parent="/".join(parts[:-1]) if parts[:-1] else "#",
    )


def _get_node_text(entry: TarInfo):
    if entry.isdir():
        return unf_utils.name_from_path(entry.name)

    file_size = unf_utils.printable_file_size(entry.size or 0)

    return f"{unf_utils.name_from_path(entry.name)} ({file_size})"
