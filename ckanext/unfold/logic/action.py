from __future__ import annotations

from dataclasses import asdict
from html import escape
from typing import Any

from ckan import types
from ckan.logic import validate
from ckan.plugins import toolkit as tk

import ckanext.unfold.config as unf_config
import ckanext.unfold.exception as unf_exception
import ckanext.unfold.index as unf_index
import ckanext.unfold.logic.schema as unf_schema
import ckanext.unfold.types as unf_types
import ckanext.unfold.utils as unf_utils


@tk.side_effect_free
@validate(unf_schema.get_archive_structure)
def get_archive_structure(
    context: types.Context, data_dict: dict[str, str]
) -> dict[str, Any]:
    """Return archive tree nodes for the jstree widget.

    The archive URL and format are read from the resource itself (via
    ``resource_show``, which also enforces authorization) rather than from the
    request, so the caller cannot point the server at an arbitrary URL.

    Two modes, decided by ``ckanext.unfold.expand_nodes_threshold``:

    * ``full`` - archives with at most that many entries: every node is
      returned flat (with ``parent``) and opened.
    * ``lazy`` - larger archives: only the direct children of ``parent``
      (default ``#``, the root) are returned, at most ``limit`` of them
      (default ``ckanext.unfold.page_size``); ``children_total`` and
      ``has_more`` tell the widget whether to offer a "show more" row.
      Folders carry ``children: true`` and are requested when opened.

    Returns ``{"error": message}`` when the archive cannot be read.
    """
    try:
        resource, resource_view = _load_resource_and_view(context, data_dict)
        index = unf_utils.get_archive_index(resource, resource_view)
    except unf_exception.UnfoldError as e:
        return {"error": str(e)}

    if index.total <= unf_config.get_expand_nodes_threshold():
        return {
            "mode": "full",
            "total": index.total,
            "nodes": [_serialize_node(n, opened=True) for n in index.all_nodes()],
        }

    parent = data_dict.get("parent") or unf_index.ROOT
    limit = int(data_dict.get("limit") or unf_config.get_page_size())
    children = index.children_of(parent)

    return {
        "mode": "lazy",
        "total": index.total,
        "parent": parent,
        "children_total": len(children),
        "has_more": len(children) > limit,
        "nodes": [
            _serialize_node(n, opened=False, flat=False) for n in children[:limit]
        ],
    }


@tk.side_effect_free
@validate(unf_schema.search_archive_structure)
def search_archive_structure(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    """Find entries whose path contains ``q``.

    Returns the first ``limit`` matching entries (``results``, each with
    its full path), the folder ids that must be opened to reveal them
    (``ids``, parents before children), the total number of matches, and
    whether the result was truncated.
    """
    try:
        resource, resource_view = _load_resource_and_view(context, data_dict)
        index = unf_utils.get_archive_index(resource, resource_view)
    except unf_exception.UnfoldError as e:
        return {"error": str(e)}

    limit = data_dict.get("limit") or unf_index.DEFAULT_SEARCH_LIMIT
    result = index.search(data_dict["q"], limit)

    return {
        "ids": result.ids,
        "matches": result.matches,
        "truncated": result.truncated,
        "results": [
            {
                "id": n.id,
                "text": n.text,
                "icon": n.icon,
                "is_dir": n.icon == unf_index.FOLDER_ICON,
                "size": str(n.data.get("size") or ""),
                "modified_at": str(n.data.get("modified_at") or ""),
            }
            for n in result.results
        ],
    }


def _load_resource_and_view(
    context: types.Context, data_dict: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    resource = tk.get_action("resource_show")(context, {"id": data_dict["id"]})
    resource_view: dict[str, Any] = {}

    if data_dict.get("view_id"):
        resource_view = tk.get_action("resource_view_show")(
            context, {"id": data_dict["view_id"]}
        )

        if resource_view.get("resource_id") != resource["id"]:
            raise unf_exception.UnfoldError("Error. View does not belong to resource")

    return resource, resource_view


def _serialize_node(
    node: unf_types.Node, opened: bool, flat: bool = True
) -> dict[str, Any]:
    """Turn a node into jstree JSON.

    Names and metadata come from the archive and are untrusted; jstree
    renders ``text`` as HTML, so everything is escaped here.
    """
    data = asdict(node)
    data["text"] = escape(node.text)

    size = escape(str(node.data.get("size") or ""))
    modified_at = escape(str(node.data.get("modified_at") or ""))

    if size or modified_at:
        data["text"] += "<span class='unfold-node-metadata'>"

        if size:
            data["text"] += f' <span class="unfold-node-size">{size}</span>'

        if modified_at:
            data["text"] += (
                f' <span class="unfold-node-modified-at">{modified_at}</span>'
            )

        data["text"] += "</span>"

    data["state"] = {"opened": opened}

    if not flat:
        # children of one folder are returned nested under it; jstree must
        # not try to resolve `parent` ids that are not part of the payload
        data.pop("parent", None)

    return data
