from __future__ import annotations

import logging
from typing import Any, Optional
from io import BytesIO

import requests
import rarfile
from rarfile import Error as RarError
from rarfile import RarInfo

import ckan.plugins.toolkit as tk


import ckanext.unfold.types as unf_types
import ckanext.unfold.utils as unf_utils

log = logging.getLogger(__name__)


def build_directory_tree(
    filepath: str, remote: Optional[bool] = False
) -> list[unf_types.Node]:
    try:
        if remote:
            file_list = get_rarlist_from_url(filepath)
        else:
            with rarfile.RarFile(filepath) as archive:
                if archive.needs_password():
                    return []

                file_list: list[RarInfo] = archive.infolist()
    except RarError as e:
        log.error(f"Error openning archive: {e}")
        return []
    except requests.RequestException as e:
        log.error(f"Error fetching remote archive: {e}")
        return []

    nodes: list[unf_types.Node] = []

    for entry in file_list:
        nodes.append(_build_node(entry))

    return nodes


def _build_node(entry: RarInfo) -> unf_types.Node:
    parts = [p for p in entry.filename.split("/") if p]
    name = unf_utils.name_from_path(entry.filename)
    fmt = "" if entry.isdir() else unf_utils.get_format_from_name(name)

    return unf_types.Node(
        id=entry.filename or "",
        text=unf_utils.name_from_path(entry.filename),
        icon="fa fa-folder" if entry.isdir() else unf_utils.get_icon_by_format(fmt),
        state={"opened": True},
        parent="/".join(parts[:-1]) + "/" if parts[:-1] else "#",
        data=_prepare_table_data(entry),
    )


def _prepare_table_data(entry: RarInfo) -> dict[str, Any]:
    name = unf_utils.name_from_path(entry.filename)
    fmt = "" if entry.isdir() else unf_utils.get_format_from_name(name)
    modified_at = tk.h.render_datetime(entry.mtime, with_hours=True)

    return {
        "size": unf_utils.printable_file_size(entry.compress_size)
        if entry.compress_size
        else "--",
        "type": "folder" if entry.isdir() else "file",
        "format": fmt,
        "modified_at": modified_at,
    }


def get_rarlist_from_url(url) -> list[RarInfo]:
    """Download an archive and fetch a file list. Rar file doesn't allow us
    to download it partially and fetch only file list."""
    resp = requests.get(url)

    return rarfile.RarFile(BytesIO(resp.content)).infolist()
