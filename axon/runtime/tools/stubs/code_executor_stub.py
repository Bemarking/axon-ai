"""CodeExecutor stub — simulates code execution without running anything."""

from __future__ import annotations

from typing import Any, ClassVar

from axon.runtime.tools.base_tool import BaseTool, ToolResult


class CodeExecutorStub(BaseTool):
    """STUB: Simulates sandboxed code execution.

    Returns a fake stdout/stderr/exit_code response.
    Does NOT actually evaluate or execute any code.
    """

    TOOL_NAME: ClassVar[str] = "CodeExecutor"
    IS_STUB: ClassVar[bool] = True
    DEFAULT_TIMEOUT: ClassVar[float] = 30.0

    def validate_config(self) -> None:
        pass  # Stubs accept any configuration

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        language = kwargs.get("language", "python")
        code = kwargs.get("code", query)

        # Simulate output based on language
        if language == "python":
            stdout = f"# Simulated Python output for:\n# {code[:80]}"
        elif language == "javascript":
            stdout = f"// Simulated JS output for:\n// {code[:80]}"
        else:
            stdout = f"[CodeExecutorStub] Would execute {language} code"

        return ToolResult(
            success=True,
            data={
                "stdout": stdout,
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 42,
                "language": language,
            },
            metadata={
                "is_stub": True,
                "language": language,
                "warning": "Code was NOT actually executed (stub mode)",
            },
        )
