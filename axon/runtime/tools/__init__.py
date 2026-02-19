"""
AXON Runtime — Tools Package
==============================
Runtime tool execution system.

Provides:

* ``BaseTool``             — abstract base for all tool implementations.
* ``ToolResult``           — standardised return type.
* ``RuntimeToolRegistry``  — instance-based registry.
* ``ToolDispatcher``       — bridge from ``IRUseTool`` to execution.

Quick start::

    from axon.runtime.tools import create_default_registry, ToolDispatcher

    registry = create_default_registry()  # loads all stubs
    dispatcher = ToolDispatcher(registry)

    result = await dispatcher.dispatch(ir_use_tool)
"""

from __future__ import annotations

from axon.runtime.tools.base_tool import BaseTool, ToolResult
from axon.runtime.tools.dispatcher import ToolDispatcher
from axon.runtime.tools.registry import RuntimeToolRegistry

__all__ = [
    "BaseTool",
    "RuntimeToolRegistry",
    "ToolDispatcher",
    "ToolResult",
    "create_default_registry",
]


def create_default_registry(
    *, mode: str = "stub",
) -> RuntimeToolRegistry:
    """Create a registry pre-loaded with tool implementations.

    Args:
        mode: ``"stub"`` — Phase 4 fakes (default).
              ``"real"`` — Production backends (Phase 5/6).
              ``"hybrid"`` — Stubs first, real backends override
              where available (recommended for development).

    Returns:
        A ``RuntimeToolRegistry`` ready for use.
    """
    registry = RuntimeToolRegistry()

    if mode == "stub":
        from axon.runtime.tools.stubs import register_all_stubs

        register_all_stubs(registry)

    elif mode == "real":
        from axon.runtime.tools.backends import register_all_backends

        register_all_backends(registry)

    elif mode == "hybrid":
        # Load stubs first, then override with real backends
        # where dependencies / API keys are available.
        from axon.runtime.tools.backends import register_all_backends
        from axon.runtime.tools.stubs import register_all_stubs

        register_all_stubs(registry)
        register_all_backends(registry)

    else:
        raise ValueError(
            f"Unknown mode '{mode}'. "
            "Supported: 'stub', 'real', 'hybrid'."
        )

    return registry
