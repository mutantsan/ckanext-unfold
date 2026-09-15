import ckan.plugins.toolkit as tk

CONF_CACHE_ENABLE = "ckanext.unfold.enable_cache"
CONF_MAX_FILE_SIZE = "ckanext.unfold.max_file_size"
CONF_EXPAND_NODES_THRESHOLD = "ckanext.unfold.expand_nodes_threshold"
CONF_CONTEXT_MENU = "ckanext.unfold.show_context_menu_default"
CONF_PAGE_SIZE = "ckanext.unfold.page_size"
CONF_REQUEST_TIMEOUT = "ckanext.unfold.request_timeout"
CONF_CACHE_TTL = "ckanext.unfold.cache_ttl"
CONF_ZIP_TAIL_BLOCK_SIZE = "ckanext.unfold.zip_tail_block_size"
CONF_MAX_ENTRIES = "ckanext.unfold.max_entries"
CONF_MAX_DECOMPRESSED_SIZE = "ckanext.unfold.max_decompressed_size"


def is_cache_enabled() -> bool:
    """Check if caching is enabled in the configuration."""
    return tk.config[CONF_CACHE_ENABLE]


def get_max_file_size() -> int:
    return tk.config[CONF_MAX_FILE_SIZE]


def get_expand_nodes_threshold() -> int:
    """Get the threshold for expanding nodes in the UI tree view."""
    return tk.config[CONF_EXPAND_NODES_THRESHOLD]


def get_context_menu_default() -> bool:
    """Get the default setting for showing context menu in the UI tree view."""
    return tk.config[CONF_CONTEXT_MENU]


def get_page_size() -> int:
    """Number of children of one folder sent per request for large archives."""
    return tk.config[CONF_PAGE_SIZE]


def get_request_timeout() -> int:
    """Per-request HTTP timeout (connect and read), in seconds."""
    return tk.config[CONF_REQUEST_TIMEOUT]


def get_cache_ttl() -> int:
    """How long a resource's Redis-cached archive index stays valid, in seconds."""
    return tk.config[CONF_CACHE_TTL]


def get_zip_tail_block_size() -> int:
    """Size, in bytes, of the suffix Range request used to probe a remote zip."""
    return tk.config[CONF_ZIP_TAIL_BLOCK_SIZE]


def get_max_entries() -> int:
    """Maximum number of entries read from one archive."""
    return tk.config[CONF_MAX_ENTRIES]


def get_max_decompressed_size() -> int:
    """Maximum decompressed size, in bytes, allowed while reading a compressed tar."""
    return tk.config[CONF_MAX_DECOMPRESSED_SIZE]
