"""
AXON Runtime — FileReader Backend (Local Filesystem)
=====================================================
Read files from the local filesystem with security boundaries.

No external dependencies — pure stdlib.

Configuration keys (via ``config`` dict):

* ``base_path``           — Root directory to restrict reads (default: cwd).
* ``max_size_mb``         — Max file size in megabytes (default: ``10``).
* ``allowed_extensions``  — Whitelist of extensions without dot,
                            e.g. ``["py", "txt", "json"]``.
                            ``None`` = allow all (default).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, ClassVar

from axon.runtime.tools.base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
_BYTES_PER_MB = 1_048_576


class FileReaderLocal(BaseTool):
    """Read files from the local filesystem with path-traversal protection.

    Security features:

    * Reads are confined to ``base_path`` (no ``../../`` escapes).
    * Configurable size limit prevents OOM on large files.
    * Optional extension whitelist.

    Example::

        tool = FileReaderLocal({"base_path": "/home/user/data"})
        result = await tool.execute("report.md")
        print(result.data["content"])
    """

    TOOL_NAME: ClassVar[str] = "FileReader"
    IS_STUB: ClassVar[bool] = False
    DEFAULT_TIMEOUT: ClassVar[float] = 5.0

    # ── Lifecycle ────────────────────────────────────────────

    def validate_config(self) -> None:
        """Resolve and validate the base path."""
        raw = self.config.get("base_path", ".")
        self._base_path = Path(raw).resolve()

        if not self._base_path.exists():
            raise ValueError(
                f"FileReaderLocal base_path does not exist: "
                f"{self._base_path}"
            )

        if not self._base_path.is_dir():
            raise ValueError(
                f"FileReaderLocal base_path is not a directory: "
                f"{self._base_path}"
            )

    # ── Execution ────────────────────────────────────────────

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        """Read a file and return its contents.

        Args:
            query:     File path (absolute or relative to *base_path*).
            encoding:  Text encoding (default ``"utf-8"``).

        Returns:
            ``ToolResult`` with ``data`` containing ``content``,
            ``filepath``, ``size_bytes``, and ``extension``.
        """
        encoding: str = kwargs.get("encoding", "utf-8")
        max_size_mb: float = self.config.get("max_size_mb", 10)

        # ── Resolve path ──────────────────────────────────
        raw_path = Path(query)
        if raw_path.is_absolute():
            file_path = raw_path.resolve()
        else:
            file_path = (self._base_path / raw_path).resolve()

        # ── Security: path-traversal guard ────────────────
        try:
            file_path.relative_to(self._base_path)
        except ValueError:
            logger.warning(
                "Path traversal blocked: '%s' escapes base '%s'",
                query, self._base_path,
            )
            return ToolResult(
                success=False,
                data=None,
                error=(
                    f"Access denied: path resolves outside base directory "
                    f"({self._base_path})"
                ),
            )

        # ── Existence check ───────────────────────────────
        if not file_path.exists():
            return ToolResult(
                success=False,
                data=None,
                error=f"File not found: {file_path}",
            )

        if not file_path.is_file():
            return ToolResult(
                success=False,
                data=None,
                error=f"Not a regular file: {file_path}",
            )

        # ── Size check ────────────────────────────────────
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / _BYTES_PER_MB

        if size_mb > max_size_mb:
            return ToolResult(
                success=False,
                data=None,
                error=(
                    f"File too large: {size_mb:.2f} MB "
                    f"(limit: {max_size_mb} MB)"
                ),
            )

        # ── Extension whitelist ───────────────────────────
        allowed: list[str] | None = self.config.get("allowed_extensions")
        ext = file_path.suffix.lstrip(".")

        if allowed is not None and ext not in allowed:
            return ToolResult(
                success=False,
                data=None,
                error=(
                    f"Extension '.{ext}' not allowed. "
                    f"Permitted: {allowed}"
                ),
            )

        # ── Read file ─────────────────────────────────────
        try:
            content = file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                data=None,
                error=(
                    f"Cannot decode file as {encoding} — "
                    f"the file may be binary"
                ),
            )
        except OSError as exc:
            return ToolResult(
                success=False,
                data=None,
                error=f"OS error reading file: {exc}",
            )

        logger.debug(
            "Read %d bytes from %s", size_bytes, file_path,
        )

        return ToolResult(
            success=True,
            data={
                "content": content,
                "filepath": str(file_path),
                "size_bytes": size_bytes,
                "extension": f".{ext}" if ext else "",
                "line_count": content.count("\n") + 1,
            },
            metadata={
                "is_stub": False,
                "encoding": encoding,
            },
        )
