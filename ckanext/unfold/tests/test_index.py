"""Tests for the folder index. No CKAN runtime needed."""

from dataclasses import asdict

from ckanext.unfold import index
from ckanext.unfold.types import Node


def _node(path: str, folder: bool = False) -> Node:
    parts = [p for p in path.split("/") if p]

    return Node(
        id=path,
        text=parts[-1],
        icon=index.FOLDER_ICON if folder else "fa fa-file",
        parent="/".join(parts[:-1]) or index.ROOT,
        data={"size": "" if folder else "1.0 KB", "modified_at": ""},
    )


def test_groups_children_by_parent_and_flags_folders():
    nodes = [_node("a", True), _node("a/x.txt"), _node("a/y.txt"), _node("z.txt")]
    idx = index.ArchiveIndex.from_nodes(nodes)

    assert idx.total == 4
    assert [n.id for n in idx.children_of(index.ROOT)] == ["a", "z.txt"]
    assert [n.id for n in idx.children_of("a")] == ["a/x.txt", "a/y.txt"]
    assert idx.children_of("missing") == []

    by_id = {n.id: n for n in idx.all_nodes()}
    assert by_id["a"].children is True
    assert by_id["z.txt"].children is False


def test_creates_missing_ancestor_folders():
    """tar/7z/rar may list files without directory entries."""
    idx = index.ArchiveIndex.from_nodes([_node("a/b/c.txt"), _node("a/d.txt")])

    ids = {n.id for n in idx.all_nodes()}
    assert ids == {"a", "a/b", "a/b/c.txt", "a/d.txt"}
    assert idx.total == 4

    by_id = {n.id: n for n in idx.all_nodes()}
    assert by_id["a"].parent == index.ROOT
    assert by_id["a/b"].parent == "a"
    assert by_id["a/b"].icon == index.FOLDER_ICON
    assert by_id["a/b"].children is True


def test_sorts_folders_first_then_case_insensitive():
    nodes = [_node("b.txt"), _node("A.txt"), _node("zdir", True), _node("zdir/f")]
    idx = index.ArchiveIndex.from_nodes(nodes)

    assert [n.id for n in idx.children_of(index.ROOT)] == ["zdir", "A.txt", "b.txt"]


def test_drops_duplicate_ids_first_wins():
    first = _node("dup.txt")
    idx = index.ArchiveIndex.from_nodes([first, _node("dup.txt")])

    assert idx.total == 1
    assert idx.all_nodes()[0] is first


def test_search_returns_ancestors_of_matches_in_order():
    idx = index.ArchiveIndex.from_nodes(
        [_node("assets/img/logo.PNG"), _node("assets/css/site.css"), _node("readme.md")]
    )

    result = idx.search("png")

    assert result.ids == ["assets", "assets/img"]
    assert result.matches == 1
    assert result.truncated is False
    assert [n.id for n in result.results] == ["assets/img/logo.PNG"]


def test_search_is_truncated_at_limit():
    nodes = [_node(f"d{i}/file{i}.log") for i in range(10)]
    idx = index.ArchiveIndex.from_nodes(nodes)

    result = idx.search(".log", limit=3)

    assert result.matches == 10
    assert result.truncated is True
    assert result.ids == ["d0", "d1", "d2"]


def test_search_no_matches():
    idx = index.ArchiveIndex.from_nodes([_node("a/b.txt")])

    assert asdict(idx.search("zzz")) == {
        "ids": [],
        "matches": 0,
        "truncated": False,
        "results": [],
    }


def test_search_paths_returns_first_matches_and_total():
    matched, matches = index.search_paths(["a/x.txt", "b/x.txt", "c.md"], "x.txt", 1)

    assert matched == ["a/x.txt"]
    assert matches == 2
