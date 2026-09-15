"""Expected listings of the small fixture archives, one per format.

Each entry is ``(id, parent, icon, size, modified_at)`` in the order the
adapter returns nodes. Dates are rendered in UTC, CKAN's default display
timezone. Regenerate by printing ``helpers.summarize(tree)`` for a fixture
after checking the change is intended.
"""

NODES: dict[str, list[tuple[str, str, str, str, str]]] = {
    "zip": [
        ("test_archive", "#", "fa fa-folder", "", "31/08/2023 - 08:44"),
        (
            "test_archive/folder 1",
            "test_archive",
            "fa fa-folder",
            "",
            "31/08/2023 - 08:44",
        ),
        (
            "test_archive/folder 1/folder 3",
            "test_archive/folder 1",
            "fa fa-folder",
            "",
            "31/08/2023 - 08:44",
        ),
        (
            "test_archive/folder 1/folder 3/test.bmp",
            "test_archive/folder 1/folder 3",
            "fa fa-file-image",
            "",
            "31/08/2023 - 08:44",
        ),
        (
            "test_archive/folder 1/test.docx",
            "test_archive/folder 1",
            "fa fa-file-word",
            "",
            "31/08/2023 - 08:44",
        ),
        (
            "test_archive/folder 1/test.txt",
            "test_archive/folder 1",
            "fa fa-file-text",
            "",
            "31/08/2023 - 08:44",
        ),
        (
            "test_archive/folder 1/test.xlsx",
            "test_archive/folder 1",
            "fa fa-file-excel",
            "5.1 KB",
            "31/08/2023 - 08:44",
        ),
        (
            "test_archive/folder 2",
            "test_archive",
            "fa fa-folder",
            "",
            "31/08/2023 - 08:44",
        ),
        (
            "test_archive/folder 2/test.docx",
            "test_archive/folder 2",
            "fa fa-file-word",
            "",
            "31/08/2023 - 08:44",
        ),
        (
            "test_archive/folder 2/test.txt",
            "test_archive/folder 2",
            "fa fa-file-text",
            "",
            "31/08/2023 - 08:44",
        ),
        (
            "test_archive/folder 2/test.xlsx",
            "test_archive/folder 2",
            "fa fa-file-excel",
            "5.1 KB",
            "31/08/2023 - 08:44",
        ),
    ],
    "zipx": [
        ("sample.html", "#", "fa fa-file-code", "59.0 B", "06/01/2008 - 20:55"),
        ("Welcome.class", "#", "fa fa-file-code", "302.0 B", "04/01/2008 - 23:04"),
        ("Welcome.java", "#", "fa fa-file-code", "97.0 B", "04/01/2008 - 23:04"),
        ("sample.css", "#", "fa fa-file-code", "166.0 B", "06/01/2008 - 21:54"),
    ],
    "7z": [
        ("sample-1", "#", "fa fa-folder", "", "31/12/2022 - 04:43"),
        (
            "sample-1/sample-1.webp",
            "sample-1",
            "fa fa-file-image",
            "718.6 KB",
            "30/12/2022 - 20:58",
        ),
        (
            "sample-1/sample-1_1.webp",
            "sample-1",
            "fa fa-file-image",
            "",
            "30/12/2022 - 20:56",
        ),
        (
            "sample-1/sample-5 (1).jpg",
            "sample-1",
            "fa fa-file-image",
            "",
            "31/12/2022 - 04:36",
        ),
        (
            "sample-1/sample-5.webp",
            "sample-1",
            "fa fa-file-image",
            "",
            "30/12/2022 - 20:58",
        ),
    ],
    "tar": [
        ("sample-1", "#", "fa fa-folder", "", "31/12/2022 - 04:43"),
        (
            "sample-1/sample-1.webp",
            "sample-1",
            "fa fa-file-image",
            "353.2 KB",
            "30/12/2022 - 20:58",
        ),
        (
            "sample-1/sample-1_1.webp",
            "sample-1",
            "fa fa-file-image",
            "353.2 KB",
            "30/12/2022 - 20:56",
        ),
        (
            "sample-1/sample-5 (1).jpg",
            "sample-1",
            "fa fa-file-image",
            "209.9 KB",
            "31/12/2022 - 04:36",
        ),
        (
            "sample-1/sample-5.webp",
            "sample-1",
            "fa fa-file-image",
            "155.3 KB",
            "30/12/2022 - 20:58",
        ),
    ],
    "tar.gz": [
        ("test_archive.tar", "#", "fa fa-file-archive", "1.1 MB", "20/02/2025 - 14:05")
    ],
    "tar.xz": [
        ("test_archive.tar", "#", "fa fa-file-archive", "1.1 MB", "20/02/2025 - 14:05")
    ],
    "tar.bz2": [
        ("test_archive.tar", "#", "fa fa-file-archive", "1.1 MB", "20/02/2025 - 14:05")
    ],
    "rar": [
        (
            "test_archive/folder 1/folder 3/test.bmp",
            "test_archive/folder 1/folder 3",
            "fa fa-file-image",
            "",
            "31/08/2023 - 05:44",
        ),
        (
            "test_archive/folder 1/test.docx",
            "test_archive/folder 1",
            "fa fa-file-word",
            "",
            "31/08/2023 - 05:44",
        ),
        (
            "test_archive/folder 1/test.txt",
            "test_archive/folder 1",
            "fa fa-file-text",
            "",
            "31/08/2023 - 05:44",
        ),
        (
            "test_archive/folder 1/test.xlsx",
            "test_archive/folder 1",
            "fa fa-file-excel",
            "5.1 KB",
            "31/08/2023 - 05:44",
        ),
        (
            "test_archive/folder 2/folder 2",
            "test_archive/folder 2",
            "fa fa-file",
            "",
            "31/08/2023 - 10:20",
        ),
        (
            "test_archive/folder 2/test.docx",
            "test_archive/folder 2",
            "fa fa-file-word",
            "",
            "31/08/2023 - 05:44",
        ),
        (
            "test_archive/folder 2/test.txt",
            "test_archive/folder 2",
            "fa fa-file-text",
            "",
            "31/08/2023 - 05:44",
        ),
        (
            "test_archive/folder 2/test.xlsx",
            "test_archive/folder 2",
            "fa fa-file-excel",
            "5.1 KB",
            "31/08/2023 - 05:44",
        ),
        (
            "test_archive/folder 1/folder 3",
            "test_archive/folder 1",
            "fa fa-folder",
            "",
            "31/08/2023 - 05:44",
        ),
        (
            "test_archive/folder 1",
            "test_archive",
            "fa fa-folder",
            "",
            "31/08/2023 - 05:44",
        ),
        (
            "test_archive/folder 2",
            "test_archive",
            "fa fa-folder",
            "",
            "31/08/2023 - 10:20",
        ),
        ("test_archive", "#", "fa fa-folder", "", "31/08/2023 - 12:49"),
        (
            "test_archive/folder 3",
            "test_archive",
            "fa fa-folder",
            "",
            "31/08/2023 - 12:49",
        ),
    ],
    "deb": [
        ("debian-binary", "#", "fa fa-file", "4.0 B", ""),
        ("control.tar.xz", "#", "fa fa-file-archive", "6.4 KB", ""),
        ("data.tar.xz", "#", "fa fa-file-archive", "1.4 MB", ""),
    ],
    "ar": [("text.txt", "#", "fa fa-file-text", "1.0 B", "")],
    "a": [
        ("file0.txt", "#", "fa fa-file-text", "5.0 B", ""),
        ("file1.bin", "#", "fa fa-file", "2.0 B", ""),
    ],
    "lib": [
        ("x64\\Release\\pch.obj", "#", "fa fa-file", "3.6 KB", ""),
        ("x64\\Release\\MiniLib.obj", "#", "fa fa-file", "1.8 KB", ""),
    ],
}
