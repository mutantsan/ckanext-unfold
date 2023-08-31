from __future__ import annotations

import math


def get_icon_by_format(fmt: str) -> str:
    default_icon = "fa fa-file"
    icons = {
        ("csv",): "fa fa-file-csv",
        ("txt", "tsv", "ini", "nfo"): "fa fa-file-text",
        ("xls", "xlsx"): "fa fa-file-excel",
        ("doc", "docx"): "fa  fa-file-word",
        ("png", "jpeg", "jpg", "svg", "bmp"): "fa fa-file-image",
        ("7z", "rar", "zip", "gzip", "gz", "tar", "deb", "cbr"): "fa fa-file-archive",
        ("pdf",): "fa fa-file-pdf",
        ("json", "xhtml", "py", "css", "rs", "html", "php", "sql"): "fa fa-file-code",
        ("xml", "dtd"): "fa fa-file-contract",
        ("mp3", "wav"): "fa fa-file-audio",
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
