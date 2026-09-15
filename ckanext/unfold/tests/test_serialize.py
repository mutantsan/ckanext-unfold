"""jstree serialisation of nodes in the API."""

from ckanext.unfold.logic import action
from ckanext.unfold.types import Node


def _node(**data) -> Node:
    return Node(
        id="dir/x.txt", text="x.txt", icon="fa fa-file-text", parent="dir", data=data
    )


def test_untrusted_names_and_metadata_are_returned_as_plain_text():
    """Nothing here embeds `text`/`data` in HTML, so nothing needs escaping:
    the widget renders `text` through jstree's `core.force_text` (a real DOM
    text node, see `unfold-init-jstree.js`) and builds the metadata spans in
    JS with `textContent`. A hostile name or metadata string is returned
    byte-for-byte; it is the client's job never to treat it as markup."""
    node = Node(
        id="<b>x</b>.txt",
        text='<img src=x onerror="alert(1)">.txt',
        icon="fa fa-file",
        parent="#",
        data={"size": "<i>1 KB</i>", "modified_at": "1 & 2"},
    )

    out = action._serialize_node(node, opened=True)

    assert out["text"] == '<img src=x onerror="alert(1)">.txt'
    assert out["id"] == "<b>x</b>.txt"
    assert out["data"] == {"size": "<i>1 KB</i>", "modified_at": "1 & 2"}


def test_metadata_stays_plain_data_not_markup():
    out = action._serialize_node(
        _node(size="5.1 KB", modified_at="01/01/2024 - 10:00"), opened=True
    )

    assert out["text"] == "x.txt"
    assert out["data"] == {"size": "5.1 KB", "modified_at": "01/01/2024 - 10:00"}
    assert out["state"] == {"opened": True}
    assert out["parent"] == "dir"


def test_empty_metadata_is_returned_as_is():
    out = action._serialize_node(_node(size="", modified_at=""), opened=False)

    assert out["text"] == "x.txt"
    assert out["data"] == {"size": "", "modified_at": ""}
    assert out["state"] == {"opened": False}


def test_nested_payload_drops_parent():
    out = action._serialize_node(
        _node(size="", modified_at=""), opened=False, flat=False
    )

    assert "parent" not in out
