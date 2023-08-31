from . import rar, _7z, zip

ADAPTERS = {
    "rar": rar.build_directory_tree,
    "cbr": rar.build_directory_tree,
    "7z": _7z.build_directory_tree,
    "zip": zip.build_directory_tree,
}
