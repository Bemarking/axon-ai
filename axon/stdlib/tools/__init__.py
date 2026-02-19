"""
AXON Standard Library — Built-in Tools
=======================================
8 pre-defined tool specifications from the AXON spec §8.4.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from axon.stdlib.tools.definitions import ALL_TOOLS

if TYPE_CHECKING:
    from axon.stdlib.base import StdlibRegistry


def register_all(registry: StdlibRegistry) -> None:
    """Register all built-in tools with the stdlib registry."""
    for tool in ALL_TOOLS:
        registry.register("tools", tool)


__all__ = ["register_all", "ALL_TOOLS"]
