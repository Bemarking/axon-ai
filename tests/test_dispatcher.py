"""Unit tests for ToolDispatcher."""

from __future__ import annotations

import asyncio
from typing import Any, ClassVar

import pytest

from axon.compiler.ir_nodes import IRUseTool
from axon.runtime.tools.base_tool import BaseTool, ToolResult
from axon.runtime.tools.dispatcher import ToolDispatcher
from axon.runtime.tools.registry import RuntimeToolRegistry


# ── Test tools ───────────────────────────────────────────────────


class EchoTool(BaseTool):
    """Returns the query as data."""

    TOOL_NAME: ClassVar[str] = "Echo"
    IS_STUB: ClassVar[bool] = True

    def validate_config(self) -> None:
        pass  # test stub

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        return ToolResult(
            success=True,
            data={"echo": query},
            metadata={"is_stub": True},
        )


class SlowTool(BaseTool):
    """Sleeps for 10 seconds — used to test timeouts."""

    TOOL_NAME: ClassVar[str] = "Slow"
    IS_STUB: ClassVar[bool] = True
    DEFAULT_TIMEOUT: ClassVar[float] = 0.1  # very short

    def validate_config(self) -> None:
        pass  # test stub

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        await asyncio.sleep(10)
        return ToolResult(success=True, data=None)


class FailingTool(BaseTool):
    """Raises an exception on execute."""

    TOOL_NAME: ClassVar[str] = "Failing"
    IS_STUB: ClassVar[bool] = True

    def validate_config(self) -> None:
        pass  # test stub

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        raise RuntimeError("Intentional failure")


# ── Helpers ──────────────────────────────────────────────────────


def _make_dispatcher(*tool_classes: type[BaseTool]) -> ToolDispatcher:
    registry = RuntimeToolRegistry()
    for cls in tool_classes:
        registry.register(cls)
    return ToolDispatcher(registry)


def _make_ir(name: str, argument: str = "hello") -> IRUseTool:
    return IRUseTool(tool_name=name, argument=argument)


# ═════════════════════════════════════════════════════════════════
#  Tests
# ═════════════════════════════════════════════════════════════════


class TestDispatchSuccess:
    @pytest.mark.asyncio
    async def test_dispatch_returns_tool_result(self) -> None:
        dispatcher = _make_dispatcher(EchoTool)
        result = await dispatcher.dispatch(_make_ir("Echo", "ping"))
        assert result.success is True
        assert result.data == {"echo": "ping"}


class TestDispatchErrors:
    @pytest.mark.asyncio
    async def test_tool_not_found(self) -> None:
        dispatcher = _make_dispatcher(EchoTool)
        result = await dispatcher.dispatch(_make_ir("Nonexistent"))
        assert result.success is False
        assert "not found" in (result.error or "").lower()

    @pytest.mark.asyncio
    async def test_timeout(self) -> None:
        dispatcher = _make_dispatcher(SlowTool)
        result = await dispatcher.dispatch(_make_ir("Slow"))
        assert result.success is False
        assert "timed out" in (result.error or "").lower()

    @pytest.mark.asyncio
    async def test_execution_error_wrapped(self) -> None:
        dispatcher = _make_dispatcher(FailingTool)
        result = await dispatcher.dispatch(_make_ir("Failing"))
        assert result.success is False
        assert "Intentional failure" in (result.error or "")


class TestDispatchMetadata:
    @pytest.mark.asyncio
    async def test_stub_warning_in_metadata(self) -> None:
        dispatcher = _make_dispatcher(EchoTool)
        result = await dispatcher.dispatch(_make_ir("Echo"))
        assert result.metadata.get("is_stub") is True
