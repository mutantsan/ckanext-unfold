from __future__ import annotations

import json
import logging
from typing import Any, Optional

import ckan.lib.uploader as uploader

import ckanext.unfold.adapters as unf_adapters
import ckanext.unfold.types as unf_types
import ckanext.unfold.utils as unf_utils

log = logging.getLogger(__name__)


def get_archive_tree(resource: dict[str, Any]) -> list[unf_types.Node]:
    remote = False

    if resource.get("url_type") == "upload":
        upload = uploader.get_resource_uploader(resource)
        filepath = upload.get_path(resource["id"])
    else:
        if not resource.get("url"):
            return []

        filepath = resource["url"]
        remote = True

    tree = unf_utils.get_archive_structure(resource["id"])

    if not tree:
        tree = parse_archive(resource["format"].lower(), filepath, remote)
        unf_utils.save_archive_structure(tree, resource["id"])

    return tree


def parse_archive(
    fmt: str, filepath: str, remote: Optional[bool] = False
) -> list[unf_types.Node]:
    if fmt not in unf_adapters.ADAPTERS:
        raise TypeError(f"No adapter for `{fmt}` archives")

    return unf_adapters.ADAPTERS[fmt](filepath, remote=remote)
