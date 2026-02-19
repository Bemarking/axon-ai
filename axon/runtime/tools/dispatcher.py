"""
AXON Runtime — Tool Dispatcher
================================
Bridge between the compiler IR (``IRUseTool``) and the runtime
tool system (``BaseTool`` via ``RuntimeToolRegistry``).

The Executor calls ``ToolDispatcher.dispatch()`` whenever a compiled
step contains a tool invocation.  The dispatcher:

1. Resolves the tool name → ``BaseTool`` implementation via the registry.
2. Applies the tool's configured timeout.
3. Returns a ``ToolResult`` back to the Executor.

This is the *only* integration point between compile-time metadata
(``IRToolSpec``) and runtime execution (``BaseTool.execute``).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from axon.compiler.ir_nodes import IRUseTool
from axon.runtime.tools.base_tool import BaseTool, ToolResult
from axon.runtime.tools.registry import RuntimeToolRegistry

logger = logging.getLogger(__name__)


class ToolDispatcher:
    """Dispatches ``IRUseTool`` nodes to registered ``BaseTool`` instances.

    Usage::

        registry = RuntimeToolRegistry()
        register_all_stubs(registry)   # Phase 4
        dispatcher = ToolDispatcher(registry)

        result = await dispatcher.dispatch(ir_use_tool, context={})
    """

    def __init__(
        self,
        registry: RuntimeToolRegistry,
        *,
        default_config: dict[str, Any] | None = None,
    ) -> None:
        """
        Args:
            registry:       The tool registry to look up implementations.
            default_config: Fallback config dict passed to tools that
                            don't have step-level config overrides.
        """
        self._registry = registry
        self._default_config = default_config or {}

    # ── Main dispatch ────────────────────────────────────────────

    async def dispatch(
        self,
        ir_use_tool: IRUseTool,
        *,
        context: dict[str, Any] | None = None,
        config_override: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Dispatch an IR tool invocation to the registered backend.

        Args:
            ir_use_tool:     The ``IRUseTool`` node from a compiled step.
            context:         Execution context (prior step results, etc.).
            config_override: Step-level config that overrides defaults.

        Returns:
            A ``ToolResult`` from the executed tool.
        """
        tool_name = ir_use_tool.tool_name
        query = ir_use_tool.argument
        config = {**self._default_config, **(config_override or {})}

        logger.debug("Dispatching tool '%s' with query: %s", tool_name, query)

        # Resolve tool from registry
        try:
            tool = self._registry.get(tool_name, config or None)
        except KeyError as exc:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool not found: {exc}",
                metadata={"tool_name": tool_name},
            )

        # Warn if stub
        if tool.IS_STUB:
            logger.warning(
                "⚠️  Using STUB for '%s' — data is simulated", tool_name
            )

        # Execute with timeout
        timeout = tool.DEFAULT_TIMEOUT
        try:
            result = await asyncio.wait_for(
                tool.execute(query, **(context or {})),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                data=None,
                error=(
                    f"Tool '{tool_name}' timed out "
                    f"after {timeout}s"
                ),
                metadata={
                    "tool_name": tool_name,
                    "timeout_seconds": timeout,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Tool '%s' raised an exception", tool_name)
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' failed: {exc}",
                metadata={"tool_name": tool_name},
            )

        # Inject standard metadata
        result.metadata.setdefault("tool_name", tool_name)
        result.metadata.setdefault("is_stub", tool.IS_STUB)

        return result

    # ── Convenience ──────────────────────────────────────────────

    @property
    def registry(self) -> RuntimeToolRegistry:
        """The underlying tool registry."""
        return self._registry

    def __repr__(self) -> str:
        return f"<ToolDispatcher registry={self._registry!r}>"
