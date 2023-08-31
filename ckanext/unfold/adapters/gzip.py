from __future__ import annotations

from ckan import model as model
import ckanext.unfold.types as unf_types


def build_directory_tree(filepath: str):
    return [_build_node(_get_file_name(filepath))]


def _get_file_name(filepath: str) -> str:
    """We don't have a solution for gzip preview yet..."""
    parts = filepath.split("/")
    resource_id = "".join(parts[-3:])

    resource = model.Resource.get(resource_id)

    return resource.url


def _build_node(name) -> unf_types.Node:
    return unf_types.Node(
        id=name,
        text=name,
        icon="fa fa-file",
        state={"opened": True},
        parent="#",
    )
