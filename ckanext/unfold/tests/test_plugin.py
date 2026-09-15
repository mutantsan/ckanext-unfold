"""The plugin's IResourceView and IResourceController hooks."""

import pytest

from ckanext.unfold import utils
from ckanext.unfold.plugin import UnfoldPlugin


@pytest.fixture
def plugin() -> UnfoldPlugin:
    return UnfoldPlugin()


@pytest.fixture
def invalidated(monkeypatch) -> list[str]:
    """Resource ids whose cache the plugin asked to drop."""
    calls: list[str] = []
    monkeypatch.setattr(
        utils.UnfoldCacheManager,
        "delete",
        classmethod(lambda cls, resource_id: calls.append(resource_id)),
    )

    return calls


@pytest.mark.parametrize(
    ("fmt", "expected"),
    [("zip", True), ("TAR.GZ", True), ("deb", True), ("csv", False), ("", False)],
)
def test_can_view_follows_the_adapter_registry(plugin, fmt: str, expected: bool):
    assert plugin.can_view({"resource": {"format": fmt}}) is expected


def test_view_info(plugin):
    info = plugin.info()

    assert info["name"] == "unfold_view"
    assert info["iframed"] is False
    assert set(info["schema"]) == {"file_url", "archive_pass", "show_context_menu"}


def test_new_upload_invalidates_the_cache(plugin, invalidated):
    current = {"id": "res", "url": "old.zip", "url_type": "upload"}
    plugin.before_resource_update(
        {}, current, {"id": "res", "url_type": "upload", "upload": object()}
    )

    assert invalidated == ["res"]


def test_editing_an_upload_without_a_new_file_keeps_the_cache(plugin, invalidated):
    current = {"id": "res", "url": "old.zip", "url_type": "upload"}
    plugin.before_resource_update(
        {}, current, {"id": "res", "url_type": "upload", "name": "renamed"}
    )

    assert invalidated == []


def test_changed_link_invalidates_the_cache(plugin, invalidated):
    current = {"id": "res", "url": "http://archives.test/a.zip", "url_type": ""}
    plugin.before_resource_update(
        {}, current, {"id": "res", "url_type": "", "url": "http://archives.test/b.zip"}
    )

    assert invalidated == ["res"]


def test_deleting_a_resource_invalidates_the_cache(plugin, invalidated):
    plugin.before_resource_delete({}, {"id": "res"}, [])

    assert invalidated == ["res"]
