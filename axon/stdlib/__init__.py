"""
AXON Standard Library
======================
Built-in personas, flows, anchors, and tools for the AXON language.

The stdlib provides pre-defined IR nodes that the compiler resolves
when encountering ``import axon.{namespace}.{Name}`` statements.

Usage::

    from axon.stdlib import StdlibRegistry

    registry = StdlibRegistry()
    persona = registry.resolve("personas", "Analyst")  # → IRPersona
    anchor  = registry.resolve("anchors", "NoHallucination")  # → IRAnchor
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from axon.stdlib.base import (
    StdlibAnchor,
    StdlibFlow,
    StdlibPersona,
    StdlibRegistry,
    StdlibTool,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "StdlibRegistry",
    "StdlibPersona",
    "StdlibAnchor",
    "StdlibFlow",
    "StdlibTool",
]
