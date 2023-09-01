from __future__ import annotations

import json
import logging
from typing import Any

import ckan.lib.uploader as uploader
import requests
from requests.exceptions import RequestException

import ckanext.unfold.adapters as unf_adapters
import ckanext.unfold.types as unf_types
import ckanext.unfold.utils as unf_utils

log = logging.getLogger(__name__)


def get_archive_tree(resource: dict[str, Any]) -> str | None:
    if resource.get("url_type") == "upload":
        upload = uploader.get_resource_uploader(resource)
        filepath = upload.get_path(resource["id"])
    else:
        # TODO: implement remote resource support
        if resource.get("url"):
            try:
                resp = requests.get(resource["url"])
            except RequestException as e:
                log.error("Error fetching data for resource: %s", resource["url"])
            else:
                data = resp.text

    tree = unf_utils.get_archive_structure(resource["id"])

    if not tree:
        tree = parse_archive(
            resource["format"].lower(), filepath
        )
        unf_utils.save_archive_structure(tree, resource["id"])

    return json.dumps(tree) if tree else None


def parse_archive(fmt: str, filepath) -> list[unf_types.Node]:
    if fmt not in unf_adapters.ADAPTERS:
        raise TypeError(f"No adapter for `{fmt}` archives")

    return unf_adapters.ADAPTERS[fmt](filepath)
