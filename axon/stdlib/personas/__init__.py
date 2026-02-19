"""
AXON Standard Library — Built-in Personas
==========================================
8 pre-defined cognitive identities from the AXON spec §8.1.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from axon.stdlib.personas.definitions import ALL_PERSONAS

if TYPE_CHECKING:
    from axon.stdlib.base import StdlibRegistry


def register_all(registry: StdlibRegistry) -> None:
    """Register all built-in personas with the stdlib registry."""
    for persona in ALL_PERSONAS:
        registry.register("personas", persona)


__all__ = ["register_all", "ALL_PERSONAS"]
