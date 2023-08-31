from __future__ import annotations

import logging
import json

import requests
from requests.exceptions import RequestException

from typing import Any

import ckan.lib.uploader as uploader

import ckanext.unfold.adapters as unf_adapters

log = logging.getLogger(__name__)


def get_archive_tree(resource: dict[str, Any]) -> Any:
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

    return json.dumps(parse_archive(resource["format"].lower(), filepath))


def parse_archive(fmt: str, filepath):
    if fmt not in unf_adapters.ADAPTERS:
        raise TypeError(f"No adapter for `{fmt}` archives")

    return unf_adapters.ADAPTERS[fmt](filepath)
