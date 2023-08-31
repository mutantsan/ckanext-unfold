from __future__ import annotations

from typing import TypedDict

import rarfile
from rarfile import RarInfo

import ckanext.unfold.utils as unf_utils


class Node(TypedDict):
    id: str
    text: str
    icon: str
    state: dict[str, bool]
    parent: str


def build_directory_tree(filepath: str):
    with rarfile.RarFile(filepath) as archive:
        file_list: list[RarInfo] = archive.infolist()

    nodes: list[Node] = []

    for entry in file_list:
        nodes.append(_build_node(entry))

    return nodes


def _build_node(entry: RarInfo) -> Node:
    parts = [p for p in entry.filename.split("/") if p]
    name = unf_utils.name_from_path(entry.filename)
    fmt = "folder" if entry.isdir() else unf_utils.get_format_from_name(name)

    return Node(
        id=entry.filename or "",
        text=_get_node_text(entry),
        icon="fa fa-folder" if entry.isdir() else unf_utils.get_icon_by_format(fmt),
        state={"opened": True},
        parent="/".join(parts[:-1]) + "/" if parts[:-1] else "#",
    )


def _get_node_text(entry: RarInfo):
    if entry.isdir():
        return unf_utils.name_from_path(entry.filename)

    file_size = unf_utils.printable_file_size(entry.compress_size or 0)

    return f"{unf_utils.name_from_path(entry.filename)} ({file_size})"
