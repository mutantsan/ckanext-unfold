from __future__ import annotations

from typing import Any, Optional, TypedDict


class Node(TypedDict, total=False):
    id: str
    text: str
    icon: str
    state: dict[str, bool]
    parent: str
    data: Optional[dict[str, Any]]
