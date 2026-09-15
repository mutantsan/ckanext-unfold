"""Shared helpers for the unfold test suite."""

from __future__ import annotations

import contextlib
import os
import re
from collections.abc import Iterator

import requests_mock

from ckanext.unfold import index, types, utils

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BASE_URL = "http://archives.test/"

#: entries each fixture archive lists, folders included
FORMAT_NODE_COUNTS = {
    "rar": 13,
    "cbr": 38,
    "7z": 5,
    "zip": 11,
    "zipx": 4,
    "jar": 76,
    "tar": 5,
    "tar.gz": 1,
    "tar.xz": 1,
    "tar.bz2": 1,
    "rpm": 355,
    "deb": 3,
    "ar": 1,
    "a": 2,
    "lib": 2,
}


def read_fixture(name: str) -> bytes:
    with open(os.path.join(DATA_DIR, name), "rb") as fp:
        return fp.read()


def range_response(data: bytes):
    """Build a requests_mock callback that serves ``data`` with Range support.

    Honors ``bytes=a-b``, ``bytes=a-`` and suffix ``bytes=-n`` requests so the
    ZIP tail fast-path (206 + Content-Range) is exercised; a request without a
    Range falls back to a full 200 response.
    """
    size = len(data)

    def _callback(request, context):
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", request.headers.get("Range", ""))

        if not match or match.group(1) == match.group(2) == "":
            context.status_code = 200
            context.headers["Content-Length"] = str(size)
            return data

        first, last = match.group(1), match.group(2)

        if first == "":
            start, end = max(0, size - int(last)), size - 1
        else:
            start = int(first)
            end = min(int(last), size - 1) if last else size - 1

        chunk = data[start : end + 1]
        context.status_code = 206
        context.headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        context.headers["Content-Length"] = str(len(chunk))

        return chunk

    return _callback


def range_rejecting_response(data: bytes):
    """Build a callback that rejects any Range request with 416.

    Mimics servers (e.g. some Werkzeug-served downloads) that reply
    ``416 Requested Range Not Satisfiable`` to a suffix range larger than the
    file instead of returning the whole file. A request without a Range gets a
    full 200 response.
    """
    size = len(data)

    def _callback(request, context):
        if request.headers.get("Range"):
            context.status_code = 416
            return b""

        context.status_code = 200
        context.headers["Content-Length"] = str(size)
        return data

    return _callback


@contextlib.contextmanager
def served(name: str, data: bytes | None = None) -> Iterator[requests_mock.Mocker]:
    """Serve ``data`` (default: the fixture called ``name``) at ``BASE_URL + name``.

    ``real_http=True`` lets every other request through untouched: CKAN
    actions under test here (``resource_show``, auth checks, ...) can
    themselves reach Solr over HTTP while the block is open, not just
    during fixture setup before it, so the mock must not blanket-block
    unmatched requests the way the plain ``requests_mock`` fixture does.
    """
    body = read_fixture(name) if data is None else data

    with requests_mock.Mocker(real_http=True) as mocker:
        mocker.get(BASE_URL + name, content=range_response(body))
        yield mocker


def assert_valid_tree(nodes: list[types.Node]) -> None:
    """Check the invariants jstree and the folder index rely on.

    Adapters may omit directory entries (tar, 7z, rar, ar), so a parent
    need not be in ``nodes`` itself, but it must be the id's own folder
    path, and once indexed every parent must resolve to a real node.
    """
    assert nodes, "adapter returned no nodes"

    ids = [node.id for node in nodes]
    assert len(ids) == len(set(ids)), "duplicate node ids"

    for node in nodes:
        assert isinstance(node, types.Node)
        assert node.id, "empty node id"
        assert not node.id.endswith("/"), f"id keeps a trailing slash: {node.id!r}"

        parts = [p for p in node.id.split("/") if p]
        expected_parent = "/".join(parts[:-1]) or index.ROOT
        assert node.parent == expected_parent, (
            f"{node.id!r} has parent {node.parent!r}, expected {expected_parent!r}"
        )

        assert node.icon, f"{node.id!r} has no icon"
        assert isinstance(node.data.get("size"), str)
        assert isinstance(node.data.get("modified_at"), str)

    indexed = index.ArchiveIndex.from_nodes(nodes)
    known = {node.id for node in indexed.all_nodes()}

    assert known >= set(ids), "index dropped nodes"

    for node in indexed.all_nodes():
        assert node.parent == index.ROOT or node.parent in known, (
            f"{node.id!r} has unresolved parent {node.parent!r}"
        )


def summarize(nodes: list[types.Node]) -> list[tuple[str, str, str, str, str]]:
    """Reduce nodes to the fields a snapshot compares: id, parent, icon, size, date."""
    return [
        (n.id, n.parent, n.icon, n.data["size"], n.data["modified_at"]) for n in nodes
    ]


def build_tree(fmt: str, url: str) -> list[types.Node]:
    adapter = utils.get_adapter_for_resource({"format": fmt})
    assert adapter is not None

    return adapter({}, {}, filepath=url).build_archive_tree()
