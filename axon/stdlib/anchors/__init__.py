"""
AXON Standard Library — Built-in Anchors
==========================================
8 pre-defined hard constraints from the AXON spec §8.3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from axon.stdlib.anchors.definitions import ALL_ANCHORS

if TYPE_CHECKING:
    from axon.stdlib.base import StdlibRegistry


def register_all(registry: StdlibRegistry) -> None:
    """Register all built-in anchors with the stdlib registry."""
    for anchor in ALL_ANCHORS:
        registry.register("anchors", anchor)


__all__ = ["register_all", "ALL_ANCHORS"]
