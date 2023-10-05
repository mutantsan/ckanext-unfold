from typing import Any

import ckan.plugins.toolkit as tk
import ckan.types as types


def resource_view_id_exists(resource_view_id: str, context: types.Context) -> Any:
    """Ensures that the resource_view with a given id exists."""

    model = context["model"]
    session = context["session"]

    if not session.query(model.ResourceView).get(resource_view_id):
        raise tk.Invalid("Resource view not found.")

    return resource_view_id
