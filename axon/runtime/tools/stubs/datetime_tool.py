"""DateTimeTool — real implementation wrapping stdlib executor."""

from __future__ import annotations

from typing import Any, ClassVar

from axon.runtime.tools.base_tool import BaseTool, ToolResult


class DateTimeTool(BaseTool):
    """REAL: Temporal reasoning — current date, time, timestamps.

    Wraps ``axon.stdlib.tools.executors.datetime_execute`` in the
    ``BaseTool`` interface.  Handles queries like ``"now"``,
    ``"today"``, ``"timestamp"``, ``"weekday"``, etc.

    This is NOT a stub — ``IS_STUB = False``.
    """

    TOOL_NAME: ClassVar[str] = "DateTimeTool"
    IS_STUB: ClassVar[bool] = False
    DEFAULT_TIMEOUT: ClassVar[float] = 1.0

    def validate_config(self) -> None:
        # DateTimeTool needs no config
        pass

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        from axon.stdlib.tools.executors import datetime_execute

        q = query.strip()
        result_str = datetime_execute(q)

        return ToolResult(
            success=True,
            data={
                "query": q,
                "result": result_str,
            },
            metadata={"is_stub": False},
        )
