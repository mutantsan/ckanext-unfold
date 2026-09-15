"""Adapter lookup, the adapter signal, and small helpers."""

import pytest

from ckanext.unfold import exception, utils
from ckanext.unfold.adapters import adapter_registry, tar
from ckanext.unfold.adapters.zip import ZipAdapter


class CustomAdapter(ZipAdapter):
    pass


@pytest.fixture
def subscribe():
    """Connect a receiver to the adapter signal for the test's duration."""
    receivers = []

    def connect(receiver):
        utils.get_adapter_for_resource_signal.connect(receiver)
        receivers.append(receiver)
        return receiver

    yield connect

    for receiver in receivers:
        utils.get_adapter_for_resource_signal.disconnect(receiver)


def test_registry_lookup_is_case_insensitive():
    assert utils.get_adapter_for_resource({"format": "ZIP"}) is adapter_registry["zip"]
    assert utils.get_adapter_for_resource({"format": "Tar.GZ"}) is tar.TarGzAdapter
    assert utils.get_adapter_for_resource({"format": "csv"}) is None
    assert utils.get_adapter_for_resource({"format": ""}) is None


def test_signal_receiver_can_provide_an_adapter(subscribe):
    subscribe(lambda resource: CustomAdapter if resource["format"] == "csv" else None)

    assert utils.get_adapter_for_resource({"format": "csv"}) is CustomAdapter
    # None from every receiver falls through to the registry
    assert utils.get_adapter_for_resource({"format": "zip"}) is adapter_registry["zip"]


def test_signal_receiver_returning_false_leaves_the_registry_in_charge(subscribe):
    """``False`` stops consulting receivers; it does not disable the format."""
    subscribe(lambda resource: False)

    assert utils.get_adapter_for_resource({"format": "zip"}) is adapter_registry["zip"]
    assert utils.get_adapter_for_resource({"format": "csv"}) is None


def test_get_archive_tree_reports_unknown_format():
    resource = {"format": "CSV", "url": "http://archives.test/x.csv"}

    with pytest.raises(exception.UnfoldError, match="No adapter for `csv` archives"):
        utils.get_archive_tree(resource, {})


@pytest.mark.parametrize(
    ("fmt", "icon"),
    [
        ("png", "fa fa-file-image"),
        (".PNG", "fa fa-file-image"),
        ("tar", "fa fa-file-archive"),
        ("csv", "fa fa-file-csv"),
        ("md", utils.DEFAULT_ICON),
        ("", utils.DEFAULT_ICON),
    ],
)
def test_get_icon_by_format(fmt: str, icon: str):
    assert utils.get_icon_by_format(fmt) == icon


@pytest.mark.parametrize(
    ("fmt", "icon"),
    [
        ("png", "fa fa-file-image format-png"),
        (".PNG", "fa fa-file-image format-png"),
        ("csv", "fa fa-file-csv format-csv"),
        # unknown extension: falls back to the default icon, keeps its class
        # (a theme may still style `.format-md` even without a dedicated
        # font-awesome icon for it)
        ("md", f"{utils.DEFAULT_ICON} format-md"),
        # no extension at all: nothing to key a format class on
        ("", utils.DEFAULT_ICON),
    ],
)
def test_file_icon(fmt: str, icon: str):
    assert utils.file_icon(fmt) == icon


def test_name_and_format_from_path():
    assert utils.name_from_path("a/b/c.txt") == "c.txt"
    assert utils.name_from_path("a/b/") == "b"
    assert utils.name_from_path("") == ""
    assert utils.name_from_path(None) == ""
    assert utils.get_format_from_name("c.txt") == ".txt"
    assert utils.get_format_from_name("Makefile") == ""
