from __future__ import annotations

import logging
from typing import Any

from ckan.lib import files, uploader

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

        return self.get_node_list()

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
        """Read a locally uploaded resource's bytes via CKAN storage.

        The size is already enforced up front against the resource metadata in
        ``validate_size_limit``.
        """
        upload = uploader.get_resource_uploader(self.resource)
        location = upload.get_path(self.resource["id"])

        try:
            return upload.storage.content(files.FileData(location))
        except files.exc.FilesError as e:
            raise unf_exception.UnfoldError(
                f"Error reading uploaded archive: {e}"
            ) from e

    @staticmethod
    def _content_length(content_length: str | None) -> int | None:
        """Parse a Content-Length header value into an int."""
        return remote.content_length(content_length)

    def get_node_list(self) -> list[unf_types.Node]:
        """Return list of nodes representing the file structure."""
        raise NotImplementedError
