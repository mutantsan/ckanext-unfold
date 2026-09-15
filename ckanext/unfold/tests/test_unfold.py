import io
import os
import re
import zipfile

import pytest

from ckanext.unfold import exception, types, utils
from ckanext.unfold.adapters import base, remote

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BASE_URL = "http://archives.test/"
ZIP64_ENTRIES = 65_536  # zipfile switches to ZIP64 records above 65,535 entries


def _range_response(data: bytes):
    """Build a requests_mock callback that serves ``data`` with Range support.

    Honors ``bytes=a-b``, ``bytes=a-`` and suffix ``bytes=-n`` requests so the
    ZIP tail fast-path (206 + Content-Range) is exercised; a request without a
    Range falls back to a full 200 response.
    """
    size = len(data)

    def _callback(request, context):
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", request.headers.get("Range", ""))

        if not match or match.group(1) == match.group(2) == "":
            context.status_code = 200
            context.headers["Content-Length"] = str(size)
            return data

        first, last = match.group(1), match.group(2)

        if first == "":
            start, end = max(0, size - int(last)), size - 1
        else:
            start = int(first)
            end = min(int(last), size - 1) if last else size - 1

        chunk = data[start : end + 1]
        context.status_code = 206
        context.headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        context.headers["Content-Length"] = str(len(chunk))

        return chunk

    return _callback


def _range_rejecting_response(data: bytes):
    """Build a callback that rejects any Range request with 416.

    Mimics servers (e.g. some Werkzeug-served downloads) that reply
    ``416 Requested Range Not Satisfiable`` to a suffix range larger than the
    file instead of returning the whole file. A request without a Range gets a
    full 200 response.
    """
    size = len(data)

    def _callback(request, context):
        if request.headers.get("Range"):
            context.status_code = 416
            return b""

        context.status_code = 200
        context.headers["Content-Length"] = str(size)
        return data

    return _callback


@pytest.fixture
def archive_url(requests_mock):
    """Serve a test data file over a mocked URL.

    Mirrors production, where archives are fetched by URL from the same host.
    Returns a callable that registers a data file and yields its URL.
    """

    def register(name: str) -> str:
        with open(os.path.join(DATA_DIR, name), "rb") as fp:
            data = fp.read()

        url = BASE_URL + name
        requests_mock.get(url, content=_range_response(data))

        return url

    return register


@pytest.mark.usefixtures("with_request_context")
@pytest.mark.parametrize(
    ("file_format", "num_nodes"),
    [
        ("rar", 13),
        ("cbr", 38),
        ("7z", 5),
        ("zip", 11),
        ("zipx", 4),
        ("jar", 76),
        ("tar", 5),
        ("tar.gz", 1),
        ("tar.xz", 1),
        ("tar.bz2", 1),
        ("rpm", 355),
        ("deb", 3),
        ("ar", 1),
        ("a", 2),
        ("lib", 2),
    ],
)
def test_build_tree(archive_url, file_format: str, num_nodes: int):
    url = archive_url(f"test_archive.{file_format}")

    adapter = utils.get_adapter_for_resource({"format": file_format})
    adapter_instance = adapter({}, {}, filepath=url)  # type: ignore
    tree = adapter_instance.build_archive_tree()

    assert len(tree) == num_nodes
    assert isinstance(tree[0], types.Node)


@pytest.mark.usefixtures("with_request_context")
def test_zip_falls_back_to_full_download_on_416(requests_mock):
    """A server that 416s the suffix-range request still builds the tree."""
    with open(os.path.join(DATA_DIR, "test_archive.zip"), "rb") as fp:
        data = fp.read()

    url = BASE_URL + "test_archive.zip"
    requests_mock.get(url, content=_range_rejecting_response(data))

    adapter = utils.get_adapter_for_resource({"format": "zip"})
    adapter_instance = adapter({}, {}, filepath=url)  # type: ignore
    tree = adapter_instance.build_archive_tree()

    assert len(tree) == 11
    assert isinstance(tree[0], types.Node)


@pytest.mark.usefixtures("with_request_context")
def test_zip_reads_local_upload_from_storage(monkeypatch):
    """A locally uploaded archive is read via CKAN storage, not over HTTP."""
    with open(os.path.join(DATA_DIR, "test_archive.zip"), "rb") as fp:
        data = fp.read()

    class FakeStorage:
        def content(self, file_data):
            return data

    class FakeUploader:
        storage = FakeStorage()

        def get_path(self, id):
            return "resource/location"

    monkeypatch.setattr(
        base.uploader, "get_resource_uploader", lambda resource: FakeUploader()
    )

    resource = {
        "id": "res-id",
        "format": "zip",
        "url_type": "upload",
        "size": str(len(data)),
    }
    adapter = utils.get_adapter_for_resource(resource)
    tree = adapter(resource, {}).build_archive_tree()  # type: ignore

    assert len(tree) == 11
    assert isinstance(tree[0], types.Node)


def test_build_complex_tree(archive_url):
    url = archive_url("test_complex_nested.zip")

    adapter = utils.get_adapter_for_resource({"format": "zip"})
    adapter_instance = adapter({}, {}, filepath=url)  # type: ignore
    tree = adapter_instance.build_archive_tree()

    assert len(tree) == 15004
    root_folders = [node for node in tree if node.parent == "#"]
    assert len(root_folders) == 4


def _zip64_archive(entries: int = ZIP64_ENTRIES, payload: bytes = b"x" * 200) -> bytes:
    """Build a ZIP64 archive in memory (flat entries, ~16 MB, ~3.3 MB directory)."""
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for i in range(entries):
            z.writestr(str(i), payload)

    return buf.getvalue()


def _bytes_requested(history, size: int) -> int:
    """Sum the bytes covered by the Range headers of recorded requests."""
    total = 0

    for request in history:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", request.headers.get("Range", ""))

        if not match:
            total += size
        elif match.group(1) == "":
            total += min(int(match.group(2)), size)
        else:
            end = int(match.group(2)) if match.group(2) else size - 1
            total += end - int(match.group(1)) + 1

    return total


@pytest.mark.usefixtures("with_request_context")
def test_zip64_remote_reads_only_the_central_directory(requests_mock):
    """A ZIP64 archive is listed by fetching its directory, not the file.

    The resource claims a size far above the limit (as a harvester recording
    a 95 GB archive would); that must not block a partial read.
    """
    data = _zip64_archive()
    url = BASE_URL + "big.zip"
    requests_mock.get(url, content=_range_response(data))

    resource = {"format": "zip", "url": url, "size": str(95 * 1024**3)}
    adapter = utils.get_adapter_for_resource(resource)
    tree = adapter(resource, {}).build_archive_tree()  # type: ignore

    assert len(tree) == ZIP64_ENTRIES
    assert all(node.parent == "#" for node in tree)

    fetched = _bytes_requested(requests_mock.request_history, len(data))
    assert fetched < len(data) // 2
    assert all(r.headers.get("Range") for r in requests_mock.request_history)


@pytest.mark.ckan_config("ckanext.unfold.max_file_size", 1024 * 1024)
@pytest.mark.usefixtures("with_request_context")
def test_zip_limit_applies_to_bytes_transferred(requests_mock, archive_url):
    """The size limit caps what is downloaded, not the archive's size."""
    # ~3.3 MB directory exceeds a 1 MB limit even though only the tail is read
    data = _zip64_archive()
    url = BASE_URL + "big.zip"
    requests_mock.get(url, content=_range_response(data))

    resource = {"format": "zip", "url": url}
    adapter = utils.get_adapter_for_resource(resource)

    with pytest.raises(exception.UnfoldError, match="exceeds maximum allowed"):
        adapter(resource, {}).build_archive_tree()  # type: ignore

    # a small archive is unaffected by the same limit
    small_url = archive_url("test_archive.zip")
    small = {"format": "zip", "url": small_url}
    tree = adapter(small, {}).build_archive_tree()  # type: ignore
    assert len(tree) == 11


@pytest.mark.usefixtures("with_request_context")
def test_zip_server_ignoring_range_falls_back_to_full_body(requests_mock):
    """A plain 200 answer (Range ignored) is parsed as the whole file."""
    with open(os.path.join(DATA_DIR, "test_archive.zip"), "rb") as fp:
        data = fp.read()

    url = BASE_URL + "test_archive.zip"
    requests_mock.get(url, content=data, headers={"Content-Length": str(len(data))})

    adapter = utils.get_adapter_for_resource({"format": "zip"})
    tree = adapter({}, {}, filepath=url).build_archive_tree()  # type: ignore

    assert len(tree) == 11


@pytest.mark.ckan_config("ckanext.unfold.max_file_size", 1024)
@pytest.mark.usefixtures("with_request_context")
def test_zip_server_ignoring_range_is_capped(requests_mock):
    """Without Range support the whole body counts against the limit."""
    with open(os.path.join(DATA_DIR, "test_archive.zip"), "rb") as fp:
        data = fp.read()

    url = BASE_URL + "test_archive.zip"
    # no Content-Length: the streaming guard must catch it
    requests_mock.get(url, content=data)

    adapter = utils.get_adapter_for_resource({"format": "zip"})

    with pytest.raises(exception.UnfoldError, match="exceeds maximum allowed"):
        adapter({}, {}, filepath=url).build_archive_tree()  # type: ignore


def test_remote_range_file_reads_across_blocks(requests_mock):
    data = bytes(range(256)) * 40  # 10,240 bytes
    url = BASE_URL + "blob"
    requests_mock.get(url, content=_range_response(data))

    remote_file = remote.RemoteRangeFile(
        url, len(data), max_bytes=len(data), block_size=4096
    )

    remote_file.seek(4000)
    # crosses a block boundary, but the whole span comes in one request,
    # aligned outwards to block boundaries (0 .. 8191)
    assert remote_file.read(300) == data[4000:4300]
    assert remote_file.requests_made == 1
    assert remote_file.bytes_fetched == 8192

    assert remote_file.seek(-16, io.SEEK_END) == len(data) - 16
    assert remote_file.read() == data[-16:]
    assert remote_file.requests_made == 2
    assert remote_file.bytes_fetched == len(data)  # last (partial) block

    # already-fetched bytes are served from memory
    remote_file.seek(100)
    assert remote_file.read(50) == data[100:150]
    assert remote_file.requests_made == 2
