from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Core.Graph.BaseNode import BaseNode

RUNTIME_NODE_REGISTRY: dict[int, BaseNode] = {}