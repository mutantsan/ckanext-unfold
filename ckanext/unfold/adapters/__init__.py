from . import rar, _7z, zip, gzip

ADAPTERS = {
    "rar": rar.build_directory_tree,
    "cbr": rar.build_directory_tree,
    "7z": _7z.build_directory_tree,
    "zip": zip.build_directory_tree,
    "gz": gzip.build_directory_tree,
    "gzip": gzip.build_directory_tree
}
