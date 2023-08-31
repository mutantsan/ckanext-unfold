from __future__ import annotations

from typing import TypedDict


class Node(TypedDict):
    id: str
    text: str
    icon: str
    state: dict[str, bool]
    parent: str
