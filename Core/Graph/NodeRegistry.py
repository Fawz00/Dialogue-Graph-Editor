from __future__ import annotations
from typing import TypeVar

from Core.Graph.BaseNode import BaseNode

# Registry utama
NodeT = TypeVar("NodeT", bound=BaseNode)

NODE_REGISTRY: dict[str, type[BaseNode]] = {}

def register_node(cls: type[NodeT]) -> type[NodeT]:
    """
    Decorator untuk auto-register node.
    """

    # Pastikan punya NODE_NAME
    node_name = getattr(cls, "NODE_NAME", None)

    if not node_name:
        raise ValueError(f"{cls.__name__} belum punya NODE_NAME")

    # Cegah duplicate
    if node_name in NODE_REGISTRY:
        raise ValueError(f"Duplicate NODE_NAME: {node_name}")

    NODE_REGISTRY[node_name] = cls

    return cls