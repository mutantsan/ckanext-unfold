from __future__ import annotations

import json
import logging
import pathlib
import time
from dataclasses import asdict
from typing import Any

import redis

import ckan.plugins.toolkit as tk
from ckan.lib.redis import connect_to_redis

import ckanext.unfold.adapters as unf_adapters
import ckanext.unfold.config as unf_config
import ckanext.unfold.exception as unf_exception
import ckanext.unfold.types as unf_types
from ckanext.unfold.formatting import (
    printable_file_size,  # noqa: F401 (re-exported for adapters)
)
from ckanext.unfold.index import (
    DEFAULT_SEARCH_LIMIT,
    ROOT,
    ArchiveIndex,
    SearchResult,
    build_search_result,
    search_paths,
)

DEFAULT_DATE_FORMAT = "%d/%m/%Y - %H:%M"
REDIS_CACHE_TTL = 3600 * 24  # 24 hour
log = logging.getLogger(__name__)


collect_adapters_signal = tk.signals.ckanext.signal(
    "unfold:register_format_adapters",
    "Collect adapters from subscribers",
)
get_adapter_for_resource_signal = tk.signals.ckanext.signal(
    "unfold:get_adapter_for_resource",
    "Get adapter for a given resource",
)


DEFAULT_ICON = "fa fa-file"

GROUPED_ICONS = {
    ("csv",): "fa fa-file-csv",
    ("txt", "tsv", "ini", "nfo", "log"): "fa fa-file-text",
    ("xls", "xlsx"): "fa fa-file-excel",
    ("doc", "docx"): "fa fa-file-word",
    ("ppt", "pptx", "pptm"): "fa fa-file-powerpoint",
    (
        "ai",
        "gif",
        "ico",
        "tif",
        "tiff",
        "webp",
        "png",
        "jpeg",
        "jpg",
        "svg",
        "bmp",
        "psd",
    ): "fa fa-file-image",
    (
        "7z",
        "rar",
        "zip",
        "zipx",
        "gzip",
        "gz",
        "bz2",
        "xz",
        "tgz",
        "tar",
        "deb",
        "cbr",
        "pkg",
        "apk",
    ): "fa fa-file-archive",
    ("pdf",): "fa fa-file-pdf",
    (
        "json",
        "xhtml",
        "py",
        "css",
        "rs",
        "html",
        "php",
        "sql",
        "java",
        "class",
    ): "fa fa-file-code",
    ("xml", "dtd"): "fa fa-file-contract",
    ("mp3", "wav", "wma", "aac", "flac", "mpa", "ogg"): "fa fa-file-audio",
    ("fnt", "fon", "otf", "ttf"): "fa fa-font",
    ("pub", "pem"): "fa fa-file-shield",
}

ICON_BY_FORMAT = {
    fmt: icon for formats, icon in GROUPED_ICONS.items() for fmt in formats
}


def get_icon_by_format(fmt: str) -> str:
    return ICON_BY_FORMAT.get(fmt.lstrip(".").lower(), DEFAULT_ICON)


def name_from_path(path: str | None) -> str:
    return path.rstrip("/").split("/")[-1] if path else ""


def get_format_from_name(name: str) -> str:
    return pathlib.Path(name).suffix


class UnfoldCacheManager:
    """Archive indexes in Redis, one hash per resource.

    Hash layout (key ``ckanext:unfold:index:<resource_id>``):

    * ``meta``  - JSON ``{"total": n}``
    * ``paths`` - all node ids joined with NUL, for search
    * ``c:<parent id>`` - JSON list of that folder's children

    Serving one folder is a single ``HGET``, whatever the archive size.
    """

    _conn: redis.Redis | None = None
    _PREFIX = "ckanext:unfold:index:"
    _BATCH = 1000

    @classmethod
    def _ensure_conn(cls) -> redis.Redis:
        if cls._conn is None:
            cls._conn = connect_to_redis()

        return cls._conn

    @classmethod
    def _key(cls, resource_id: str) -> str:
        return f"{cls._PREFIX}{resource_id}"

    @classmethod
    def save(cls, index: ArchiveIndex, resource_id: str) -> None:
        conn = cls._ensure_conn()
        key = cls._key(resource_id)

        mapping: dict[str, str] = {
            "meta": json.dumps({"total": index.total}),
            "paths": "\0".join(index.paths),
        }

        for parent, nodes in index.children.items():
            mapping[f"c:{parent}"] = json.dumps([asdict(n) for n in nodes])

        pipe = conn.pipeline()
        pipe.delete(key)

        items = list(mapping.items())
        for start in range(0, len(items), cls._BATCH):
            pipe.hset(key, mapping=dict(items[start : start + cls._BATCH]))

        pipe.expire(key, REDIS_CACHE_TTL)
        pipe.execute()

    @classmethod
    def exists(cls, resource_id: str) -> bool:
        return bool(cls._ensure_conn().hexists(cls._key(resource_id), "meta"))

    @classmethod
    def total(cls, resource_id: str) -> int:
        raw = cls._ensure_conn().hget(cls._key(resource_id), "meta")

        return json.loads(raw)["total"] if raw else 0  # type: ignore

    @classmethod
    def children(cls, resource_id: str, parent: str) -> list[unf_types.Node]:
        raw = cls._ensure_conn().hget(cls._key(resource_id), f"c:{parent}")

        return [unf_types.Node(**n) for n in json.loads(raw)] if raw else []  # type: ignore

    @classmethod
    def all_nodes(cls, resource_id: str) -> list[unf_types.Node]:
        data: dict[bytes, bytes] = cls._ensure_conn().hgetall(cls._key(resource_id))  # type: ignore
        nodes: list[unf_types.Node] = []

        for field, raw in data.items():
            if field.startswith(b"c:"):
                nodes.extend(unf_types.Node(**n) for n in json.loads(raw))

        return nodes

    @classmethod
    def paths(cls, resource_id: str) -> list[str]:
        raw: bytes | None = cls._ensure_conn().hget(cls._key(resource_id), "paths")  # type: ignore

        return raw.decode().split("\0") if raw else []

    @classmethod
    def delete(cls, resource_id: str) -> None:
        cls._ensure_conn().delete(cls._key(resource_id))

    @classmethod
    def close(cls) -> None:
        if not cls._conn:
            return

        cls._conn.close()
        cls._conn = None


class CachedIndex:
    """Same interface as ``ArchiveIndex``, reading from Redis on demand."""

    def __init__(self, resource_id: str) -> None:
        self.resource_id = resource_id
        self.total = UnfoldCacheManager.total(resource_id)

    def children_of(self, parent: str) -> list[unf_types.Node]:
        return UnfoldCacheManager.children(self.resource_id, parent)

    def all_nodes(self) -> list[unf_types.Node]:
        return UnfoldCacheManager.all_nodes(self.resource_id)

    def search(self, query: str, limit: int = DEFAULT_SEARCH_LIMIT) -> SearchResult:
        paths = UnfoldCacheManager.paths(self.resource_id)
        matched, matches = search_paths(paths, query, limit)

        # matched nodes live in their parents' child lists: one HGET per parent
        siblings: dict[str, dict[str, unf_types.Node]] = {}
        nodes: list[unf_types.Node] = []

        for path in matched:
            parts = [p for p in path.split("/") if p]
            parent = "/".join(parts[:-1]) or ROOT

            if parent not in siblings:
                siblings[parent] = {n.id: n for n in self.children_of(parent)}

            node = siblings[parent].get(path)

            if node is not None:
                nodes.append(node)

        return build_search_result(matched, matches, limit, nodes)


def get_archive_index(
    resource: dict[str, Any], resource_view: dict[str, Any]
) -> ArchiveIndex | CachedIndex:
    """Return the archive's folder index, building and caching it if needed."""
    cache_enabled = unf_config.is_cache_enabled()

    if cache_enabled and UnfoldCacheManager.exists(resource["id"]):
        cached = CachedIndex(resource["id"])
        log.info(
            "Resource %s: serving %s entries from the Redis index",
            resource["id"],
            cached.total,
        )
        return cached

    started = time.monotonic()
    log.info(
        "Building archive index for resource %s (%s, cache %s)",
        resource["id"],
        resource.get("url"),
        "on" if cache_enabled else "off",
    )

    nodes = get_archive_tree(resource, resource_view)
    log.info(
        "Resource %s: adapter returned %s entries in %.1fs",
        resource["id"],
        len(nodes),
        time.monotonic() - started,
    )

    index = ArchiveIndex.from_nodes(nodes)

    if cache_enabled:
        UnfoldCacheManager.save(index, resource["id"])

    log.info(
        "Resource %s: indexed %s entries in %.1fs total",
        resource["id"],
        index.total,
        time.monotonic() - started,
    )

    return index


def get_archive_tree(
    resource: dict[str, Any], resource_view: dict[str, Any]
) -> list[unf_types.Node]:
    """Build the flat node list for a resource with the matching adapter."""
    adapter_cls = get_adapter_for_resource(resource)

    if adapter_cls is None:
        res_format = resource["format"].lower()
        raise unf_exception.UnfoldError(f"No adapter for `{res_format}` archives")

    return _build_archive_tree(adapter_cls, resource_view, resource)


def _build_archive_tree(
    adapter_cls: type[unf_adapters.BaseAdapter],
    resource_view: dict[str, Any],
    resource: dict[str, Any],
    filepath: str | None = None,
) -> list[unf_types.Node]:
    adapter_instance = adapter_cls(resource, resource_view, filepath=filepath)
    return adapter_instance.build_archive_tree()


def get_adapter_for_resource(
    resource: dict[str, Any],
) -> type[unf_adapters.BaseAdapter] | None:
    res_format = resource["format"].lower()

    for _, adapter in get_adapter_for_resource_signal.send(resource):
        if adapter is None:
            continue

        if adapter is False:
            break

        return adapter

    return unf_adapters.adapter_registry.get(res_format)
