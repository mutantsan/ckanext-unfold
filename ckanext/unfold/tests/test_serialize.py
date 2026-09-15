"""jstree serialisation of nodes in the API."""

from ckanext.unfold.logic import action
from ckanext.unfold.types import Node


def _node(**data) -> Node:
    return Node(
        id="dir/x.txt", text="x.txt", icon="fa fa-file-text", parent="dir", data=data
    )


def test_untrusted_names_and_metadata_are_escaped():
    node = Node(
        id="<b>x</b>.txt",
        text='<img src=x onerror="alert(1)">.txt',
        icon="fa fa-file",
        parent="#",
        data={"size": "<i>1 KB</i>", "modified_at": "1 & 2"},
    )

    out = action._serialize_node(node, opened=True)

    assert "<img" not in out["text"]
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;.txt" in out["text"]
    assert "&lt;i&gt;1 KB&lt;/i&gt;" in out["text"]
    assert "1 &amp; 2" in out["text"]
    assert out["id"] == "<b>x</b>.txt"


def test_metadata_is_rendered_as_spans():
    out = action._serialize_node(
        _node(size="5.1 KB", modified_at="01/01/2024 - 10:00"), opened=True
    )

    assert out["text"] == (
        "x.txt<span class='unfold-node-metadata'>"
        ' <span class="unfold-node-size">5.1 KB</span>'
        ' <span class="unfold-node-modified-at">01/01/2024 - 10:00</span>'
        "</span>"
    )
    assert out["state"] == {"opened": True}
    assert out["parent"] == "dir"


def test_empty_metadata_adds_no_markup():
    out = action._serialize_node(_node(size="", modified_at=""), opened=False)

    assert out["text"] == "x.txt"
    assert out["state"] == {"opened": False}


def test_nested_payload_drops_parent():
    out = action._serialize_node(
        _node(size="", modified_at=""), opened=False, flat=False
    )

    assert "parent" not in out
