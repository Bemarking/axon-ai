"""
AXON Standard Library — Built-in Flows
=======================================
8 pre-defined cognitive pipelines from the AXON spec §8.2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from axon.stdlib.flows.definitions import ALL_FLOWS

if TYPE_CHECKING:
    from axon.stdlib.base import StdlibRegistry


def register_all(registry: StdlibRegistry) -> None:
    """Register all built-in flows with the stdlib registry."""
    for flow in ALL_FLOWS:
        registry.register("flows", flow)


__all__ = ["register_all", "ALL_FLOWS"]
