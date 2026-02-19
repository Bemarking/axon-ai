"""
AXON Runtime — CodeExecutor Backend (Subprocess)
==================================================
Execute code locally using ``subprocess`` + ``asyncio.to_thread()``.

No external dependencies — pure stdlib.

.. warning::

    Code runs **without sandboxing** on the host machine.
    Only use with trusted code in development environments.
    For production, use the Docker-based executor instead.

Configuration keys (via ``config`` dict):

* ``timeout``            — Execution timeout in seconds (default: ``10``).
* ``allowed_languages``  — Whitelist, e.g. ``["python"]``
                           (default: all supported).
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, ClassVar

from axon.runtime.tools.base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# ── Language → executable mapping ────────────────────────────
_EXECUTORS: dict[str, str] = {
    "python": "python",
    "javascript": "node",
    "bash": "bash",
}

_EXTENSIONS: dict[str, str] = {
    "python": ".py",
    "javascript": ".js",
    "bash": ".sh",
}


class CodeExecutorSubprocess(BaseTool):
    """Execute code locally via subprocess.

    Writes code to a temporary file and invokes the appropriate
    interpreter.  Uses ``asyncio.to_thread()`` so the event loop
    is never blocked.

    Example::

        tool = CodeExecutorSubprocess({"timeout": 5})
        result = await tool.execute(
            "print('Hello AXON')",
            language="python",
        )
        print(result.data["stdout"])  # "Hello AXON\\n"
    """

    TOOL_NAME: ClassVar[str] = "CodeExecutor"
    IS_STUB: ClassVar[bool] = False
    DEFAULT_TIMEOUT: ClassVar[float] = 15.0

    # ── Lifecycle ────────────────────────────────────────────

    def validate_config(self) -> None:
        """No mandatory config — optional timeout and language whitelist."""
        # Intentionally empty; stubs accept any configuration.
        # Real validation (interpreter existence) happens lazily
        # in execute() to keep construction lightweight.

    # ── Execution ────────────────────────────────────────────

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        """Execute code and return stdout/stderr/exit_code.

        Args:
            query:     The source code to execute.
            language:  Programming language (default ``"python"``).
                       Supported: ``python``, ``javascript``, ``bash``.

        Returns:
            ``ToolResult`` with ``data`` containing ``stdout``,
            ``stderr``, ``exit_code``, and ``language``.
        """
        code = query
        language = kwargs.get("language", "python").lower()
        timeout = self.config.get("timeout", 10)

        # ── Language validation ───────────────────────────
        if language not in _EXECUTORS:
            return ToolResult(
                success=False,
                data=None,
                error=(
                    f"Unsupported language: '{language}'. "
                    f"Supported: {sorted(_EXECUTORS)}"
                ),
            )

        # ── Whitelist check ───────────────────────────────
        allowed = self.config.get("allowed_languages")
        if allowed and language not in allowed:
            return ToolResult(
                success=False,
                data=None,
                error=(
                    f"Language '{language}' not in allowed list: "
                    f"{allowed}"
                ),
            )

        executor = _EXECUTORS[language]
        extension = _EXTENSIONS[language]

        # ── Write code to temp file ───────────────────────
        tmp = tempfile.NamedTemporaryFile(
            suffix=extension,
            prefix="axon_exec_",
            mode="w",
            encoding="utf-8",
            delete=False,
        )
        tmp.write(code)
        tmp.close()
        code_file = Path(tmp.name)

        try:
            return await asyncio.to_thread(
                self._run_subprocess,
                executor=executor,
                code_file=str(code_file),
                timeout=timeout,
            )

        finally:
            code_file.unlink(missing_ok=True)

    # ── Private helpers ──────────────────────────────────────

    @staticmethod
    def _run_subprocess(
        *,
        executor: str,
        code_file: str,
        timeout: int,
    ) -> ToolResult:
        """Synchronous subprocess call (runs in thread)."""
        try:
            proc = subprocess.run(  # noqa: S603
                [executor, code_file],
                capture_output=True,
                timeout=timeout,
                text=True,
            )

            return ToolResult(
                success=(proc.returncode == 0),
                data={
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exit_code": proc.returncode,
                    "language": Path(code_file).suffix.lstrip("."),
                },
                error=(
                    proc.stderr.strip() if proc.returncode != 0 else None
                ),
                metadata={
                    "is_stub": False,
                    "warning": "Executed without sandboxing",
                },
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data=None,
                error=f"Execution timed out after {timeout}s",
            )

        except FileNotFoundError:
            return ToolResult(
                success=False,
                data=None,
                error=(
                    f"Interpreter '{executor}' not found. "
                    f"Is it installed and in PATH?"
                ),
            )

        except OSError as exc:
            return ToolResult(
                success=False,
                data=None,
                error=f"OS error: {exc}",
            )
