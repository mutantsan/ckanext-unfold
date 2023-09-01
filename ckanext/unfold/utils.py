from __future__ import annotations

import json
import math

from ckan.lib.redis import connect_to_redis

import ckanext.unfold.types as unf_types


def get_icon_by_format(fmt: str) -> str:
    default_icon = "fa fa-file"
    icons = {
        ("csv",): "fa fa-file-csv",
        ("txt", "tsv", "ini", "nfo"): "fa fa-file-text",
        ("xls", "xlsx"): "fa fa-file-excel",
        ("doc", "docx"): "fa fa-file-word",
        ("ppt", "pptx", "pptm"): "fa fa-file-powerpoint",
        ("png", "jpeg", "jpg", "svg", "bmp", "psd"): "fa fa-file-image",
        ("7z", "rar", "zip", "gzip", "gz", "tar", "deb", "cbr"): "fa fa-file-archive",
        ("pdf",): "fa fa-file-pdf",
        ("json", "xhtml", "py", "css", "rs", "html", "php", "sql"): "fa fa-file-code",
        ("xml", "dtd"): "fa fa-file-contract",
        ("mp3", "wav", "wma", "aac", "flac"): "fa fa-file-audio",
    }

    for formats, icon in icons.items():
        for _format in formats:
            if _format == fmt:
                return icon

    return default_icon


def name_from_path(path: str | None) -> str:
    return path.rstrip("/").split("/")[-1] if path else ""


def get_format_from_name(name: str) -> str:
    return name.split(".")[-1]


def printable_file_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 bytes"
    size_name = ("bytes", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(float(size_bytes) / p, 1)
    return "%s %s" % (s, size_name[i])


def save_archive_structure(nodes: list[unf_types.Node], resource_id: str) -> None:
    """Save an archive structure to redis to"""
    conn = connect_to_redis()
    conn.set(f"ckanext:unfold:tree:{resource_id}", json.dumps(nodes))
    conn.close()


def get_archive_structure(resource_id: str) -> None:
    """Retrieve an archive structure from redis"""
    conn = connect_to_redis()
    data = conn.get(f"ckanext:unfold:tree:{resource_id}")
    conn.close()

    return json.loads(data) if data else None


def delete_archive_structure(resource_id: str) -> None:
    """Delete an archive structure from redis. Called on resource delete/update"""
    conn = connect_to_redis()
    conn.delete(f"ckanext:unfold:tree:{resource_id}")
    conn.close()
