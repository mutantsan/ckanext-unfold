import os

import pytest

import ckanext.unfold.adapters as unf_adapters


@pytest.mark.usefixtures("with_request_context")
def test_build_tree_from_rar():
    file_path = os.path.join(os.path.dirname(__file__), "data/test_archive.rar")

    assert unf_adapters.rar.build_directory_tree(file_path)
