"""Unit tests for BaseTool ABC and ToolResult."""

from __future__ import annotations

import asyncio
from typing import Any, ClassVar

import pytest

from axon.runtime.tools.base_tool import BaseTool, ToolResult


# ── Concrete subclass for testing ────────────────────────────────


class DummyTool(BaseTool):
    """Minimal concrete BaseTool for testing."""

    TOOL_NAME: ClassVar[str] = "DummyTool"
    IS_STUB: ClassVar[bool] = True
    DEFAULT_TIMEOUT: ClassVar[float] = 5.0

    def validate_config(self) -> None:
        pass  # accepts anything

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data={"echo": query})


class StrictTool(BaseTool):
    """BaseTool subclass that requires an ``api_key`` config."""

    TOOL_NAME: ClassVar[str] = "StrictTool"
    IS_STUB: ClassVar[bool] = False
    DEFAULT_TIMEOUT: ClassVar[float] = 10.0

    def validate_config(self) -> None:
        if "api_key" not in self.config:
            raise ValueError("Missing api_key")

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data={"key": self.config["api_key"]})


# ═════════════════════════════════════════════════════════════════
#  ToolResult
# ═════════════════════════════════════════════════════════════════


class TestToolResult:
    def test_success_result(self) -> None:
        r = ToolResult(success=True, data={"a": 1})
        assert r.success is True
        assert r.data == {"a": 1}
        assert r.error is None
        assert r.metadata == {}

    def test_error_result(self) -> None:
        r = ToolResult(success=False, data=None, error="boom")
        assert r.success is False
        assert r.error == "boom"

    def test_to_dict_minimal(self) -> None:
        r = ToolResult(success=True, data="ok")
        d = r.to_dict()
        assert d == {"success": True, "data": "ok"}
        assert "error" not in d
        assert "metadata" not in d

    def test_to_dict_full(self) -> None:
        r = ToolResult(
            success=False,
            data=None,
            error="timeout",
            metadata={"elapsed": 5.2},
        )
        d = r.to_dict()
        assert d["error"] == "timeout"
        assert d["metadata"]["elapsed"] == 5.2

    def test_metadata_default_factory(self) -> None:
        """Two results share no mutable state."""
        r1 = ToolResult(success=True, data=None)
        r2 = ToolResult(success=True, data=None)
        r1.metadata["x"] = 1
        assert "x" not in r2.metadata


# ═════════════════════════════════════════════════════════════════
#  BaseTool — contract
# ═════════════════════════════════════════════════════════════════


class TestBaseTool:
    def test_class_constants(self) -> None:
        tool = DummyTool()
        assert tool.TOOL_NAME == "DummyTool"
        assert tool.IS_STUB is True
        assert tool.DEFAULT_TIMEOUT == 5.0

    def test_convenience_properties(self) -> None:
        tool = DummyTool()
        assert tool.get_tool_name == "DummyTool"
        assert tool.get_is_stub is True

    def test_default_config(self) -> None:
        tool = DummyTool()
        assert tool.config == {}

    def test_custom_config(self) -> None:
        tool = DummyTool(config={"key": "val"})
        assert tool.config["key"] == "val"

    def test_async_execute(self) -> None:
        tool = DummyTool()
        result = asyncio.get_event_loop().run_until_complete(
            tool.execute("hello"),
        )
        assert result.success is True
        assert result.data == {"echo": "hello"}

    def test_repr_stub(self) -> None:
        r = repr(DummyTool())
        assert "DummyTool" in r
        assert "[STUB]" in r

    def test_repr_non_stub(self) -> None:
        r = repr(StrictTool(config={"api_key": "k"}))
        assert "StrictTool" in r
        assert "[STUB]" not in r


class TestBaseToolValidation:
    def test_strict_tool_missing_key(self) -> None:
        with pytest.raises(ValueError, match="Missing api_key"):
            StrictTool()

    def test_strict_tool_valid_config(self) -> None:
        tool = StrictTool(config={"api_key": "abc123"})
        assert tool.config["api_key"] == "abc123"

    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            BaseTool()  # type: ignore[abstract]
