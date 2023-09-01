from __future__ import annotations

from typing import Any, Dict

from ckan.logic.schema import validator_args

Schema = Dict[str, Any]


@validator_args
def get_preview_schema(ignore_empty, unicode_safe, url_validator) -> Schema:
    return {"file_url": [ignore_empty, unicode_safe, url_validator]}


@validator_args
def get_archive_structure(not_empty, unicode_safe, resource_id_exists) -> Schema:
    return {"id": [not_empty, unicode_safe, resource_id_exists]}
