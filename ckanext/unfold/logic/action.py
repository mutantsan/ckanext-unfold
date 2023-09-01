from ckan.logic import validate
from ckan.plugins import toolkit as tk

import ckanext.unfold.exception as unf_exception
import ckanext.unfold.helpers as unf_helpers
import ckanext.unfold.logic.schema as unf_schema


@tk.side_effect_free
@validate(unf_schema.get_archive_structure)
def get_archive_structure(context, data_dict):
    # TODO: use it, rewrite the init tree script
    # make ajax call and init it only if there's no error
    resource = tk.get_action("resource_show")(context, {"id": data_dict["id"]})

    try:
        return unf_helpers.get_archive_tree(resource)
    except unf_exception.UnfoldError as e:
        return {"error": str(e)}
