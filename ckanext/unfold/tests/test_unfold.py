import os
from io import BytesIO

import pytest

from ckanext.unfold.adapters import rar


def test_build_tree_from_rar():
    file_path = os.path.join(os.path.dirname(__file__), "data/test_archive.rar")

    assert rar.build_directory_tree(file_path)
