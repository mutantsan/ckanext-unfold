from __future__ import annotations

import logging
import os
from typing import Any

from ckan.lib import uploader

try:
    # CKAN >= 2.12 only: the file-keeper storage layer core absorbed from
    # ckanext-files. Older CKAN's uploaders never set `storage` (see
    # `_read_upload`), so the module is simply unused when it is missing.
    from ckan.lib import files
except ImportError:  # CKAN < 2.12
    files = None  # type: ignore[assignment]

import ckanext.unfold.config as unf_config
import ckanext.unfold.exception as unf_exception
import ckanext.unfold.types as unf_types
from ckanext.unfold.adapters import remote
from ckanext.unfold.adapters.remote import DEFAULT_TIMEOUT

log = logging.getLogger(__name__)

__all__ = ["DEFAULT_TIMEOUT", "BaseAdapter"]


class BaseAdapter:
    #: Set to ``True`` in adapters that can read a remote archive's index
    #: without downloading the whole file (see ``remote.open_remote``). For
    #: those the resource's declared size is not checked up front; the size
    #: limit applies to the bytes actually transferred instead, so archives
    #: far larger than the limit remain previewable.
    partial_read: bool = False

    def __init__(
        self,
        resource: dict[str, Any],
        resource_view: dict[str, Any],
        filepath: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.resource = resource
        self.resource_view = resource_view
        self.kwargs = kwargs
        self.filepath = filepath or self._get_filepath()

    def _get_filepath(self) -> str:
        resource_url = self.resource.get("url", "")

        if self.resource.get("type") == "tabledesigner":
            raise unf_exception.UnfoldError(
                "Error. Table Designer resources are not supported"
            )

        return resource_url

    @property
    def is_upload(self) -> bool:
        return self.resource.get("url_type") == "upload"

    @property
    def reads_partially(self) -> bool:
        """Whether this adapter will fetch only parts of the remote file."""
        return self.partial_read and not self.is_upload

    def build_archive_tree(self) -> list[unf_types.Node]:
        if not self.reads_partially:
            self.validate_size_limit()

        try:
            return self.get_node_list()
        except unf_exception.UnfoldError:
            raise
        except Exception as e:
            # Archive libraries raise their own errors (and plain ValueError,
            # struct.error, EOFError...) on damaged input. Only UnfoldError
            # reaches the user as a message; anything else would be a 500.
            log.exception(
                "Resource %s: could not read %s archive %s",
                self.resource.get("id"),
                self.resource.get("format"),
                self.filepath,
            )
            raise unf_exception.UnfoldError("Error. Could not read the archive") from e

    def validate_size_limit(self) -> None:
        archive_size = self.resource.get("size")

        if archive_size and isinstance(archive_size, str):
            try:
                archive_size = int(archive_size)
            except (ValueError, TypeError):
                archive_size = None

        self.enforce_size_limit(archive_size)

    def enforce_size_limit(self, size: int | None) -> None:
        """Raise if ``size`` exceeds the configured maximum archive size.

        ``None`` means the size is unknown and is allowed through.
        """
        remote.check_limit(size, unf_config.get_max_file_size())

    def get_file_content(self, url: str | None = None) -> bytes:
        """Return the resource's content as bytes.

        Locally uploaded resources are read straight from CKAN storage,
        avoiding an authenticated HTTP request to CKAN's own download endpoint
        (which fails for private datasets with 403). Remote resources are
        downloaded over HTTP.

        For remote downloads the size is enforced against the configured
        maximum: the advertised Content-Length is rejected up front, and the
        download is aborted once the bytes read exceed the limit (in case
        Content-Length is missing or wrong), so an over-limit archive is never
        fully loaded into memory.
        """
        if self.is_upload:
            return self._read_upload()

        return remote.fetch_full(
            url or self.filepath, unf_config.get_max_file_size(), DEFAULT_TIMEOUT
        )

    def _read_upload(self) -> bytes:
        """Read an uploaded resource's bytes through whatever uploader serves it.

        CKAN 2.12's file-keeper uploader exposes a ``storage``; the legacy
        ``ResourceUpload`` and extensions such as ckanext-cloudstorage or
        ckanext-s3filestore only offer ``get_path``, which may name a local
        file or a key in a remote bucket. Each shape is tried in turn, ending
        with a plain download of the resource URL for uploaders that keep
        files elsewhere.

        The size is already enforced up front against the resource metadata in
        ``validate_size_limit``; the download fallback enforces it again.
        """
        upload = uploader.get_resource_uploader(self.resource)
        resource_id = self.resource["id"]
        # `files` (and thus a `storage` attribute) only exists on CKAN >= 2.12
        storage = getattr(upload, "storage", None) if files is not None else None

        if storage is not None:
            try:
                return storage.content(files.FileData(upload.get_path(resource_id)))
            except files.exc.FilesError as e:
                raise unf_exception.UnfoldError(
                    f"Error reading uploaded archive: {e}"
                ) from e

        path = self._local_upload_path(upload)

        if path is not None:
            try:
                with open(path, "rb") as fp:
                    return fp.read()
            except OSError as e:
                raise unf_exception.UnfoldError(
                    f"Error reading uploaded archive: {e}"
                ) from e

        log.info(
            "Resource %s: uploader %s offers neither a storage nor a local file;"
            " downloading %s",
            resource_id,
            type(upload).__name__,
            self.filepath,
        )
        return remote.fetch_full(
            self.filepath, unf_config.get_max_file_size(), DEFAULT_TIMEOUT
        )

    def _local_upload_path(self, upload: Any) -> str | None:
        """Absolute path of the uploaded file, if the uploader keeps it on disk."""
        get_path = getattr(upload, "get_path", None)

        if get_path is None:
            return None

        try:
            path = get_path(self.resource["id"])
        except Exception:
            # ResourceUpload raises TypeError without a storage path and
            # ValidationError for ids it cannot map; neither is fatal here
            log.debug(
                "Resource %s: %s.get_path failed",
                self.resource["id"],
                type(upload).__name__,
                exc_info=True,
            )
            return None

        if isinstance(path, str) and os.path.isabs(path) and os.path.isfile(path):
            return path

        return None

    @staticmethod
    def _content_length(content_length: str | None) -> int | None:
        """Parse a Content-Length header value into an int."""
        return remote.content_length(content_length)

    def get_node_list(self) -> list[unf_types.Node]:
        """Return list of nodes representing the file structure."""
        raise NotImplementedError
