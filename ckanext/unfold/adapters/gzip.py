from __future__ import annotations

from typing import Any, Optional, cast

from ckan import model as model

import ckanext.unfold.types as unf_types
import ckanext.unfold.utils as unf_utils


def build_directory_tree(
    filepath: str, resource_view: dict[str, Any], remote: Optional[bool] = False
):
    resource = _get_resource(filepath)
    return [_build_node(resource)]


def _get_resource(filepath: str) -> model.Resource:
    """We don't have a solution for gzip preview yet..."""
    parts = filepath.split("/")
    resource_id = "".join(parts[-3:])

    return cast(model.Resource, model.Resource.get(resource_id))


def _build_node(resource: model.Resource) -> unf_types.Node:
    return unf_types.Node(
        id=resource.url,
        text=resource.url,
        icon="fa fa-file",
        state={"opened": True},
        parent="#",
        data=_prepare_table_data(resource),
    )


def _prepare_table_data(resource: model.Resource) -> dict[str, Any]:
    return {
        "size": unf_utils.printable_file_size(resource.size) if resource.size else "",
        "type": "file",
        "format": resource.format,
        "modified_at": "--",
    }
