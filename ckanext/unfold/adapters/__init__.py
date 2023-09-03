from functools import partial

from . import _7z, gzip, rar, rpm, tar, zip

ADAPTERS = {
    "rar": rar.build_directory_tree,
    "cbr": rar.build_directory_tree,
    "7z": _7z.build_directory_tree,
    "zip": zip.build_directory_tree,
    "zipx": zip.build_directory_tree,
    "jar": zip.build_directory_tree,
    "gz": gzip.build_directory_tree,
    "gzip": gzip.build_directory_tree,
    "tar": tar.build_directory_tree,
    "tar.gz": partial(tar.build_directory_tree, compression="gz"),
    "tar.xz": partial(tar.build_directory_tree, compression="xz"),
    "tar.bz2": partial(tar.build_directory_tree, compression="bz2"),
    "rpm": rpm.build_directory_tree,
}
