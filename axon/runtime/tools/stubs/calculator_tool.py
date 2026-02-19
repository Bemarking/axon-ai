"""Calculator tool — real implementation wrapping stdlib executor."""

from __future__ import annotations

from typing import Any, ClassVar

from axon.runtime.tools.base_tool import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """REAL: Safe mathematical expression evaluator.

    Wraps ``axon.stdlib.tools.executors.calculator_execute`` in the
    ``BaseTool`` interface.  Supports basic arithmetic, trig, logs,
    and common math constants (pi, e).

    This is NOT a stub — ``IS_STUB = False``.
    """

    TOOL_NAME: ClassVar[str] = "Calculator"
    IS_STUB: ClassVar[bool] = False
    DEFAULT_TIMEOUT: ClassVar[float] = 2.0

    def validate_config(self) -> None:
        # Calculator needs no config
        pass

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        from axon.stdlib.tools.executors import calculator_execute

        expression = query.strip()
        try:
            result_str = calculator_execute(expression)
            return ToolResult(
                success=True,
                data={
                    "expression": expression,
                    "result": result_str,
                },
                metadata={"is_stub": False},
            )
        except ValueError as exc:
            return ToolResult(
                success=False,
                data=None,
                error=str(exc),
                metadata={
                    "is_stub": False,
                    "expression": expression,
                },
            )
