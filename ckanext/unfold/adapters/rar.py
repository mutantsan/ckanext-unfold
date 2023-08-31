from __future__ import annotations

from typing import TypedDict, overload, Literal, Any
from typing_extensions import TypeAlias

import rarfile
from rarfile import RarInfo


class File(TypedDict):
    name: str


class Dir(TypedDict):
    name: str
    children: list[Node]
    childNames: dict[str, int]
    open: bool
    icon: str


Node: TypeAlias = "File | Dir"


def build_directory_tree1(filepath: str):
    with rarfile.RarFile(filepath) as archive:
        file_list: list[RarInfo] = archive.infolist()

    root = mktree(".")

    for entry in file_list:
        if not entry.filename:
            continue

        parts = [p for p in entry.filename.split("/") if p]  # type: ignore

        if entry.isdir():
            descend(root, parts)
        else:
            result = descend(root, parts[:-1])
            insert(result, parts[-1], True)

    root["children"][0]["open"] = True

    return root["children"]


def mktree(name: str) -> Dir:
    return {
        "text": name,
        "open": False,
        "icon": "fa-folder",
        "children": [],
        "childNames": {},
    }


def descend(root: Dir, parts: list[str]) -> Dir:
    first, *rest = parts

    folder = insert(root, first, False)

    return folder if not rest else descend(folder, rest)


@overload
def insert(root, name: str, isFile: Literal[False]) -> Dir:
    ...


@overload
def insert(root, name: str, isFile: Literal[True]) -> File:
    ...


def insert(root, name: str, isFile: bool) -> Node:
    if name not in root["childNames"]:
        root["children"].append(
            mktree(name)
            if not isFile
            else {
                "text": name,
                "icon": "fa-file",
            }
        )
        root["childNames"][name] = len(root["children"]) - 1

    return root["children"][root["childNames"][name]]


def build_directory_tree(filepath: str):
    with rarfile.RarFile(filepath) as archive:
        file_list: list[RarInfo] = archive.infolist()

    nodes = []

    # file_list = sorted(
    #     [f for f in file_list],
    #     key=lambda f: (len([f for f in f.filename.split("/") if f]), f.filename),
    # )

    for entry in file_list:
        nodes.append(_build_node(entry))

    # result = []
    # for node in nodes:
    #     if not node["parent"]:
    #         result.append(node)
    #     else:
    #         if node["is_dir"]:
    #             result.append(node)
    #         else:
    #             for n in result:
    #                 if n["name"] != node["parent"]:
    #                     continue
    #                 n["children"].append(node)

    return nodes


def _build_node(entry: RarInfo) -> dict[str, Any]:
    parts = [p for p in entry.filename.split("/") if p]
    name = _get_name(entry.filename)
    fmt = "folder" if entry.isdir() else _get_format_from_name(name)

    return {
        "id": entry.filename,
        "text": _get_name(entry.filename),
        "is_dir": entry.is_dir(),
        # "timestamp": entry.mtime.isoformat(),
        "size": entry.compress_size,
        "icon": "fa fa-folder" if entry.isdir() else _get_icon_by_format(fmt),
        'state' : { 'opened' : True},
        # "children": [],
        # "rarInfo": entry,
        "parent": "/".join(parts[:-1]) + "/" if parts[:-1] else "#",
    }


def _get_name(filename: str | None) -> str:
    if not filename:
        return ""
    return filename.rstrip("/").split("/")[-1]


def _get_format_from_name(name: str) -> str:
    return name.split(".")[-1]


def _get_icon_by_format(fmt: str) -> str:
    default_icon = "fa fa-file"
    icons = {
        ("csv"): "fa fa-file-csv",
        ("txt", "tsv"): "fa fa-file-text",
        ("xls", "xlsx"): "fa fa-file-excel",
        ("doc", "docx"): "fa  fa-file-word",
        ("png", "jpeg", "jpg", "svg", "bmp"): "fa fa-file-image",
        ("7z", "rar", "zip"): "fa fa-file-archive",
    }

    for formats, icon in icons.items():
        for _format in formats:
            if _format == fmt:
                return icon

    return default_icon
