"""
Tests for AXON Runtime — Real Tool Backends (Phase 5/6)
========================================================
Unit tests for all three production tool backends plus
the ``create_default_registry`` factory modes.

Tested without external services — Serper API calls
are mocked, FileReader uses a real temp directory,
and CodeExecutor runs real Python subprocess calls.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from axon.runtime.tools import create_default_registry
from axon.runtime.tools.base_tool import BaseTool, ToolResult
from axon.runtime.tools.registry import RuntimeToolRegistry


# ═══════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════


def run(coro: Any) -> Any:
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ═══════════════════════════════════════════════════════════════════
#  WebSearchSerper — mockable tests (no real API calls)
# ═══════════════════════════════════════════════════════════════════


class TestWebSearchSerper:
    """Tests for the Serper.dev WebSearch backend."""

    def _make_tool(self, **extra: Any) -> BaseTool:
        from axon.runtime.tools.backends.web_search_serper import (
            WebSearchSerper,
        )

        config = {"api_key": "test-key-123", **extra}
        return WebSearchSerper(config)

    def test_class_constants(self) -> None:
        from axon.runtime.tools.backends.web_search_serper import (
            WebSearchSerper,
        )

        assert WebSearchSerper.TOOL_NAME == "WebSearch"
        assert WebSearchSerper.IS_STUB is False

    def test_validate_config_missing_key_no_env(self) -> None:
        from axon.runtime.tools.backends.web_search_serper import (
            WebSearchSerper,
        )

        with patch.dict(os.environ, {}, clear=True):
            env = dict(os.environ)
            env.pop("SERPER_API_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="api_key"):
                    WebSearchSerper({})

    def test_validate_config_uses_env_fallback(self) -> None:
        from axon.runtime.tools.backends.web_search_serper import (
            WebSearchSerper,
        )

        with patch.dict(os.environ, {"SERPER_API_KEY": "env-key"}):
            tool = WebSearchSerper({})
            assert tool.config["api_key"] == "env-key"

    def test_validate_config_with_key(self) -> None:
        tool = self._make_tool()
        assert tool.config["api_key"] == "test-key-123"

    @patch("axon.runtime.tools.backends.web_search_serper.httpx.AsyncClient")
    def test_execute_success(self, mock_client_cls: MagicMock) -> None:
        """Mocked Serper API returns organic results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "organic": [
                {
                    "title": "Python 3.13 Released",
                    "link": "https://python.org/3.13",
                    "snippet": "New features in Python 3.13",
                    "displayedLink": "python.org",
                    "position": 1,
                },
                {
                    "title": "What's New in 3.13",
                    "link": "https://docs.python.org/3.13",
                    "snippet": "Comprehensive changelog",
                    "displayedLink": "docs.python.org",
                    "position": 2,
                },
            ],
            "searchParameters": {"time": "0.42s"},
        }
        mock_response.raise_for_status = MagicMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_ctx.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_ctx

        tool = self._make_tool()
        result = run(tool.execute("Python 3.13", max_results=2))

        assert result.success is True
        assert len(result.data) == 2
        assert result.data[0]["title"] == "Python 3.13 Released"
        assert result.data[0]["url"] == "https://python.org/3.13"
        assert result.metadata["is_stub"] is False
        assert result.metadata["provider"] == "serper"

    @patch("axon.runtime.tools.backends.web_search_serper.httpx.AsyncClient")
    def test_execute_http_error(self, mock_client_cls: MagicMock) -> None:
        """401 returns a clear error about invalid API key."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=mock_response,
        )

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_ctx.post = AsyncMock(side_effect=error)
        mock_client_cls.return_value = mock_ctx

        tool = self._make_tool()
        result = run(tool.execute("test query"))

        assert result.success is False
        assert "401" in result.error
        assert "Invalid API key" in result.error

    @patch("axon.runtime.tools.backends.web_search_serper.httpx.AsyncClient")
    def test_execute_timeout(self, mock_client_cls: MagicMock) -> None:
        """Timeout returns user-friendly message."""
        import httpx

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_ctx.post = AsyncMock(side_effect=httpx.TimeoutException("boom"))
        mock_client_cls.return_value = mock_ctx

        tool = self._make_tool()
        result = run(tool.execute("test query"))

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_repr(self) -> None:
        tool = self._make_tool()
        assert "WebSearchSerper" in repr(tool)
        assert "WebSearch" in repr(tool)
        assert "[STUB]" not in repr(tool)


# ═══════════════════════════════════════════════════════════════════
#  FileReaderLocal — real filesystem tests
# ═══════════════════════════════════════════════════════════════════


class TestFileReaderLocal:
    """Tests for the local FileReader backend."""

    def _make_tool(self, base_path: str, **extra: Any) -> BaseTool:
        from axon.runtime.tools.backends.file_reader_local import (
            FileReaderLocal,
        )

        return FileReaderLocal({"base_path": base_path, **extra})

    def test_class_constants(self) -> None:
        from axon.runtime.tools.backends.file_reader_local import (
            FileReaderLocal,
        )

        assert FileReaderLocal.TOOL_NAME == "FileReader"
        assert FileReaderLocal.IS_STUB is False

    def test_validate_config_nonexistent_path(self) -> None:
        from axon.runtime.tools.backends.file_reader_local import (
            FileReaderLocal,
        )

        with pytest.raises(ValueError, match="does not exist"):
            FileReaderLocal({"base_path": "/nonexistent/path/12345"})

    def test_read_file_success(self, tmp_path: Path) -> None:
        test_file = tmp_path / "hello.txt"
        test_file.write_text("Hello AXON!", encoding="utf-8")

        tool = self._make_tool(str(tmp_path))
        result = run(tool.execute("hello.txt"))

        assert result.success is True
        assert result.data["content"] == "Hello AXON!"
        assert result.data["size_bytes"] == len("Hello AXON!".encode())
        assert result.data["extension"] == ".txt"
        assert result.data["line_count"] == 1
        assert result.metadata["is_stub"] is False

    def test_read_file_absolute_path(self, tmp_path: Path) -> None:
        test_file = tmp_path / "abs.json"
        test_file.write_text('{"key": "value"}', encoding="utf-8")

        tool = self._make_tool(str(tmp_path))
        result = run(tool.execute(str(test_file)))

        assert result.success is True
        assert '"key"' in result.data["content"]

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        tool = self._make_tool(str(tmp_path))
        result = run(tool.execute("../../etc/passwd"))

        assert result.success is False
        assert "outside base directory" in result.error

    def test_file_not_found(self, tmp_path: Path) -> None:
        tool = self._make_tool(str(tmp_path))
        result = run(tool.execute("nonexistent.txt"))

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_file_too_large(self, tmp_path: Path) -> None:
        big_file = tmp_path / "big.bin"
        big_file.write_bytes(b"x" * (2 * 1_048_576))  # 2 MB

        tool = self._make_tool(str(tmp_path), max_size_mb=1)
        result = run(tool.execute("big.bin"))

        assert result.success is False
        assert "too large" in result.error.lower()

    def test_extension_whitelist_allows(self, tmp_path: Path) -> None:
        test_file = tmp_path / "code.py"
        test_file.write_text("x = 1", encoding="utf-8")

        tool = self._make_tool(
            str(tmp_path), allowed_extensions=["py", "txt"],
        )
        result = run(tool.execute("code.py"))
        assert result.success is True

    def test_extension_whitelist_blocks(self, tmp_path: Path) -> None:
        test_file = tmp_path / "secret.exe"
        test_file.write_text("bad", encoding="utf-8")

        tool = self._make_tool(
            str(tmp_path), allowed_extensions=["py", "txt"],
        )
        result = run(tool.execute("secret.exe"))

        assert result.success is False
        assert "not allowed" in result.error

    def test_multiline_file(self, tmp_path: Path) -> None:
        test_file = tmp_path / "multi.txt"
        test_file.write_text("line1\nline2\nline3", encoding="utf-8")

        tool = self._make_tool(str(tmp_path))
        result = run(tool.execute("multi.txt"))

        assert result.success is True
        assert result.data["line_count"] == 3


# ═══════════════════════════════════════════════════════════════════
#  CodeExecutorSubprocess — real execution tests
# ═══════════════════════════════════════════════════════════════════


class TestCodeExecutorSubprocess:
    """Tests for the subprocess CodeExecutor backend."""

    def _make_tool(self, **extra: Any) -> BaseTool:
        from axon.runtime.tools.backends.code_executor_subprocess import (
            CodeExecutorSubprocess,
        )

        return CodeExecutorSubprocess(extra)

    def test_class_constants(self) -> None:
        from axon.runtime.tools.backends.code_executor_subprocess import (
            CodeExecutorSubprocess,
        )

        assert CodeExecutorSubprocess.TOOL_NAME == "CodeExecutor"
        assert CodeExecutorSubprocess.IS_STUB is False

    def test_execute_python_success(self) -> None:
        tool = self._make_tool()
        result = run(tool.execute("print('hello AXON')"))

        assert result.success is True
        assert "hello AXON" in result.data["stdout"]
        assert result.data["exit_code"] == 0
        assert result.metadata["is_stub"] is False

    def test_execute_python_error(self) -> None:
        tool = self._make_tool()
        result = run(tool.execute("raise ValueError('boom')"))

        assert result.success is False
        assert result.data["exit_code"] != 0
        assert "ValueError" in result.data["stderr"]

    def test_execute_python_output(self) -> None:
        code = "import sys; print(2 + 2); sys.exit(0)"
        tool = self._make_tool()
        result = run(tool.execute(code))

        assert result.success is True
        assert "4" in result.data["stdout"]

    def test_unsupported_language(self) -> None:
        tool = self._make_tool()
        result = run(tool.execute("code", language="rust"))

        assert result.success is False
        assert "Unsupported language" in result.error

    def test_language_whitelist_blocked(self) -> None:
        tool = self._make_tool(allowed_languages=["python"])
        result = run(tool.execute("console.log(1)", language="javascript"))

        assert result.success is False
        assert "not in allowed list" in result.error

    def test_timeout(self) -> None:
        tool = self._make_tool(timeout=1)
        code = "import time; time.sleep(10)"
        result = run(tool.execute(code))

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_temp_file_cleanup(self) -> None:
        """Temp files should be deleted after execution."""
        tool = self._make_tool()
        before = set(
            p for p in Path(tempfile.gettempdir()).glob("axon_exec_*")
        )

        run(tool.execute("print(1)"))

        after = set(
            p for p in Path(tempfile.gettempdir()).glob("axon_exec_*")
        )

        leaked = after - before
        assert len(leaked) == 0, f"Temp file leaked: {leaked}"

    def test_no_sandboxing_warning(self) -> None:
        tool = self._make_tool()
        result = run(tool.execute("print(1)"))

        assert result.metadata.get("warning") == "Executed without sandboxing"


# ═══════════════════════════════════════════════════════════════════
#  Registry Factory — create_default_registry() modes
# ═══════════════════════════════════════════════════════════════════


class TestCreateDefaultRegistryModes:
    """Test all three registry creation modes."""

    def test_mode_stub(self) -> None:
        registry = create_default_registry(mode="stub")
        tool_cls = registry.get("WebSearch")
        assert tool_cls.IS_STUB is True

    def test_mode_real(self) -> None:
        registry = create_default_registry(mode="real")

        fr_cls = registry.get("FileReader")
        assert fr_cls.IS_STUB is False
        assert fr_cls.TOOL_NAME == "FileReader"

        ce_cls = registry.get("CodeExecutor")
        assert ce_cls.IS_STUB is False

    def test_mode_hybrid(self) -> None:
        registry = create_default_registry(mode="hybrid")

        fr_cls = registry.get("FileReader")
        assert fr_cls.IS_STUB is False

        ce_cls = registry.get("CodeExecutor")
        assert ce_cls.IS_STUB is False

        calc_cls = registry.get("Calculator")
        assert calc_cls.IS_STUB is False

    def test_mode_invalid(self) -> None:
        with pytest.raises(ValueError, match="Unknown mode"):
            create_default_registry(mode="invalid")

    def test_mode_hybrid_preserves_stubs_without_backend(self) -> None:
        """Tools without a real backend keep their stub."""
        registry = create_default_registry(mode="hybrid")

        img_cls = registry.get("ImageAnalyzer")
        assert img_cls.IS_STUB is True

    def test_mode_real_has_file_reader_and_executor(self) -> None:
        """Real mode always registers FileReader and CodeExecutor."""
        registry = create_default_registry(mode="real")

        fr = registry.get("FileReader")
        ce = registry.get("CodeExecutor")

        assert fr.TOOL_NAME == "FileReader"
        assert ce.TOOL_NAME == "CodeExecutor"


# ═══════════════════════════════════════════════════════════════════
#  Backend registration
# ═══════════════════════════════════════════════════════════════════


class TestBackendRegistration:
    """Test register_all_backends behavior."""

    def test_register_without_serper_key(self) -> None:
        from axon.runtime.tools.backends import register_all_backends

        registry = RuntimeToolRegistry()

        with patch.dict(os.environ, {}, clear=True):
            env = dict(os.environ)
            env.pop("SERPER_API_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                register_all_backends(registry)

        # WebSearch should NOT be registered (no key)
        with pytest.raises(KeyError):
            registry.get("WebSearch")

        # FileReader and CodeExecutor should always be registered
        assert registry.get("FileReader").TOOL_NAME == "FileReader"
        assert registry.get("CodeExecutor").TOOL_NAME == "CodeExecutor"

    def test_register_with_serper_key_in_config(self) -> None:
        from axon.runtime.tools.backends import register_all_backends

        registry = RuntimeToolRegistry()
        register_all_backends(
            registry, config={"serper_api_key": "test-123"},
        )

        # Verify the class was registered (don't instantiate — that
        # requires the api_key in the instance config at get()-time).
        assert "WebSearch" in registry._classes
        assert registry._classes["WebSearch"].IS_STUB is False
