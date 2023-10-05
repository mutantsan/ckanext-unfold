from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str
    text: str
    icon: str
    parent: str
    state: Optional[Dict[str, bool]] = Field(default={"opened": True})
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
