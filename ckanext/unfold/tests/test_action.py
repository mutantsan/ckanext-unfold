"""The ``get_archive_structure`` and ``search_archive_structure`` actions.

Datasets are created outside the HTTP mock: CKAN indexes them in Solr
over HTTP, which ``requests_mock`` would otherwise refuse.
"""

import pytest

import ckan.plugins.toolkit as tk
from ckan.tests import factories
from ckan.tests.helpers import call_action

from ckanext.unfold.tests.helpers import BASE_URL, served

pytestmark = [
    pytest.mark.ckan_config("ckanext.unfold.enable_cache", False),
    pytest.mark.usefixtures("with_plugins", "clean_db", "with_request_context"),
]

ARCHIVE = "test_archive.zip"


@pytest.fixture
def archive_resource():
    """A resource whose URL serves the small zip fixture while ``served`` is active."""
    return factories.Resource(url=BASE_URL + ARCHIVE, format="zip")


def test_small_archive_is_returned_whole(archive_resource):
    with served(ARCHIVE):
        result = call_action("get_archive_structure", id=archive_resource["id"])

    assert result["mode"] == "full"
    assert result["total"] == 11
    assert len(result["nodes"]) == 11

    node = next(
        n for n in result["nodes"] if n["id"] == "test_archive/folder 1/test.xlsx"
    )
    assert node["parent"] == "test_archive/folder 1"
    assert node["state"] == {"opened": True}
    assert node["text"].startswith("test.xlsx<span")
    assert '<span class="unfold-node-size">5.1 KB</span>' in node["text"]


@pytest.mark.ckan_config("ckanext.unfold.expand_nodes_threshold", 1)
def test_large_archive_is_served_folder_by_folder(archive_resource):
    with served(ARCHIVE):
        root = call_action("get_archive_structure", id=archive_resource["id"])
        page = call_action(
            "get_archive_structure",
            id=archive_resource["id"],
            parent="test_archive",
            limit=1,
        )
        rest = call_action(
            "get_archive_structure",
            id=archive_resource["id"],
            parent="test_archive",
            limit=10,
        )

    assert root["mode"] == "lazy"
    assert root["total"] == 11
    assert root["parent"] == "#"
    assert root["children_total"] == 1
    assert root["has_more"] is False
    assert [n["id"] for n in root["nodes"]] == ["test_archive"]
    assert root["nodes"][0]["children"] is True
    assert root["nodes"][0]["state"] == {"opened": False}
    assert "parent" not in root["nodes"][0]

    assert page["children_total"] == 2
    assert page["has_more"] is True
    assert [n["id"] for n in page["nodes"]] == ["test_archive/folder 1"]

    assert rest["has_more"] is False
    assert [n["id"] for n in rest["nodes"]] == [
        "test_archive/folder 1",
        "test_archive/folder 2",
    ]


def test_search_returns_matches_and_the_folders_to_open(archive_resource):
    with served(ARCHIVE):
        result = call_action(
            "search_archive_structure", id=archive_resource["id"], q="XLSX"
        )
        limited = call_action(
            "search_archive_structure", id=archive_resource["id"], q="xlsx", limit=1
        )

    assert result["matches"] == 2
    assert result["truncated"] is False
    assert result["ids"] == [
        "test_archive",
        "test_archive/folder 1",
        "test_archive/folder 2",
    ]
    assert [r["id"] for r in result["results"]] == [
        "test_archive/folder 1/test.xlsx",
        "test_archive/folder 2/test.xlsx",
    ]
    assert result["results"][0]["size"] == "5.1 KB"
    assert result["results"][0]["is_dir"] is False

    assert limited["matches"] == 2
    assert limited["truncated"] is True
    assert len(limited["results"]) == 1


def test_unsupported_format_is_an_error_payload():
    resource = factories.Resource(url=BASE_URL + "data.csv", format="csv")

    result = call_action("get_archive_structure", id=resource["id"])

    assert result == {"error": "No adapter for `csv` archives"}


def test_unreachable_archive_is_an_error_payload():
    resource = factories.Resource(url=BASE_URL + "gone.zip", format="zip")

    with served("gone.zip", b"") as mocker:
        mocker.get(BASE_URL + "gone.zip", status_code=404)
        result = call_action("get_archive_structure", id=resource["id"])

    assert list(result) == ["error"]
    assert result["error"].startswith("Error fetching")


def test_view_of_another_resource_is_rejected(archive_resource):
    other = factories.Resource(
        package_id=archive_resource["package_id"],
        url=BASE_URL + "other.zip",
        format="zip",
    )
    view = call_action(
        "resource_view_create",
        resource_id=other["id"],
        view_type="unfold_view",
        title="Unfold",
    )

    with served(ARCHIVE):
        result = call_action(
            "get_archive_structure", id=archive_resource["id"], view_id=view["id"]
        )

    assert result == {"error": "Error. View does not belong to resource"}


def test_unknown_ids_fail_validation(archive_resource):
    with pytest.raises(tk.ValidationError):
        call_action("get_archive_structure", id="does-not-exist")

    with pytest.raises(tk.ValidationError):
        call_action(
            "get_archive_structure", id=archive_resource["id"], view_id="does-not-exist"
        )

    with pytest.raises(tk.ValidationError):
        call_action("search_archive_structure", id=archive_resource["id"], q="")


def test_private_dataset_requires_read_access():
    member = factories.User()
    org = factories.Organization(users=[{"name": member["name"], "capacity": "member"}])
    dataset = factories.Dataset(owner_org=org["id"], private=True)
    resource = factories.Resource(
        package_id=dataset["id"], url=BASE_URL + ARCHIVE, format="zip"
    )

    with served(ARCHIVE):
        with pytest.raises(tk.NotAuthorized):
            call_action(
                "get_archive_structure",
                {"user": "", "ignore_auth": False},
                id=resource["id"],
            )

        result = call_action(
            "get_archive_structure",
            {"user": member["name"], "ignore_auth": False},
            id=resource["id"],
        )

    assert result["mode"] == "full"
