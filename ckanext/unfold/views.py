from __future__ import annotations


from flask import jsonify, Response, Blueprint
from flask.views import MethodView

import ckan.plugins.toolkit as tk

import ckanext.unfold.exception as unf_exception
import ckanext.unfold.helpers as unf_helpers

unfold = Blueprint("unfold", __name__)


class UnfoldGetTree(MethodView):
    def get(self) -> Response:
        resource = tk.get_action("resource_show")(
            {},
            {
                "id": tk.request.args.get("id"),
            },
        )

        status_code = 200

        try:
            data = unf_helpers.get_archive_tree(resource)
        except unf_exception.UnfoldError as e:
            data = {"error": str(e)}
            status_code = 401

        response = jsonify(data)
        response.status_code = status_code

        return response


unfold.add_url_rule(
    "/api/action/get_archive_structure", view_func=UnfoldGetTree.as_view("get_tree")
)


def get_blueprints():
    return [unfold]
