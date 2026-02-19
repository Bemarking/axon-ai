"""Unit tests for RuntimeToolRegistry."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from axon.runtime.tools.base_tool import BaseTool, ToolResult
from axon.runtime.tools.registry import RuntimeToolRegistry


# ── Test tools ───────────────────────────────────────────────────


class AlphaTool(BaseTool):
    TOOL_NAME: ClassVar[str] = "Alpha"
    IS_STUB: ClassVar[bool] = True

    def validate_config(self) -> None:
        pass  # test stub

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data="alpha")


class BetaTool(BaseTool):
    TOOL_NAME: ClassVar[str] = "Beta"
    IS_STUB: ClassVar[bool] = False

    def validate_config(self) -> None:
        pass  # test stub

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data="beta")


class AlphaRealTool(BaseTool):
    """Non-stub replacement for Alpha."""

    TOOL_NAME: ClassVar[str] = "Alpha"
    IS_STUB: ClassVar[bool] = False

    def validate_config(self) -> None:
        pass  # test stub

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data="alpha-real")


# ═════════════════════════════════════════════════════════════════
#  Registration
# ═════════════════════════════════════════════════════════════════


class TestRegistration:
    def test_register_and_has(self) -> None:
        reg = RuntimeToolRegistry()
        reg.register(AlphaTool)
        assert reg.has("Alpha")
        assert not reg.has("Nonexistent")

    def test_register_duplicate_replaces_silently(self) -> None:
        reg = RuntimeToolRegistry()
        reg.register(AlphaTool)
        reg.register(AlphaTool)  # should not raise
        assert reg.has("Alpha")

    def test_register_missing_tool_name_raises(self) -> None:
        class NoName(BaseTool):
            TOOL_NAME: ClassVar[str] = ""
            IS_STUB: ClassVar[bool] = True

            def validate_config(self) -> None:
                pass  # test stub

            async def execute(self, query: str, **kwargs: Any) -> ToolResult:
                return ToolResult(success=True, data=None)

        reg = RuntimeToolRegistry()
        with pytest.raises(ValueError, match="TOOL_NAME"):
            reg.register(NoName)


# ═════════════════════════════════════════════════════════════════
#  Getting instances
# ═════════════════════════════════════════════════════════════════


class TestGet:
    def test_get_returns_instance(self) -> None:
        reg = RuntimeToolRegistry()
        reg.register(AlphaTool)
        tool = reg.get("Alpha")
        assert isinstance(tool, AlphaTool)
        assert tool.TOOL_NAME == "Alpha"

    def test_get_caches_instance(self) -> None:
        reg = RuntimeToolRegistry()
        reg.register(AlphaTool)
        t1 = reg.get("Alpha")
        t2 = reg.get("Alpha")
        assert t1 is t2

    def test_get_with_different_config_creates_new(self) -> None:
        reg = RuntimeToolRegistry()
        reg.register(AlphaTool)
        t1 = reg.get("Alpha")
        t2 = reg.get("Alpha", config={"x": 1})
        assert t1 is not t2

    def test_get_not_found_raises(self) -> None:
        reg = RuntimeToolRegistry()
        with pytest.raises(KeyError, match="not registered"):
            reg.get("Nonexistent")


# ═════════════════════════════════════════════════════════════════
#  Replace
# ═════════════════════════════════════════════════════════════════


class TestReplace:
    def test_replace_swap(self) -> None:
        reg = RuntimeToolRegistry()
        reg.register(AlphaTool)
        old = reg.get("Alpha")
        assert old.IS_STUB is True

        reg.replace("Alpha", AlphaRealTool)
        new = reg.get("Alpha")
        assert isinstance(new, AlphaRealTool)
        assert new.IS_STUB is False

    def test_replace_clears_cache(self) -> None:
        reg = RuntimeToolRegistry()
        reg.register(AlphaTool)
        old = reg.get("Alpha")

        reg.replace("Alpha", AlphaRealTool)
        new = reg.get("Alpha")
        assert old is not new

    def test_replace_different_name_still_works(self) -> None:
        """Registry replace doesn't enforce TOOL_NAME match."""
        reg = RuntimeToolRegistry()
        reg.register(AlphaTool)
        # BetaTool has TOOL_NAME="Beta", but it's registered under "Alpha"
        reg.replace("Alpha", BetaTool)
        assert reg.has("Alpha")


# ═════════════════════════════════════════════════════════════════
#  list_tools / clear
# ═════════════════════════════════════════════════════════════════


class TestListAndClear:
    def test_list_tools(self) -> None:
        reg = RuntimeToolRegistry()
        reg.register(AlphaTool)
        reg.register(BetaTool)
        listing = reg.list_tools()
        assert listing == {"Alpha": True, "Beta": False}

    def test_clear(self) -> None:
        reg = RuntimeToolRegistry()
        reg.register(AlphaTool)
        reg.get("Alpha")  # populate cache
        reg.clear()
        assert not reg.has("Alpha")
        assert reg.list_tools() == {}
