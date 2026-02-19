"""APICall stub — simulates generic REST API calls."""

from __future__ import annotations

from typing import Any, ClassVar

from axon.runtime.tools.base_tool import BaseTool, ToolResult


class APICallStub(BaseTool):
    """STUB: Simulates a generic REST API call.

    Returns a fake HTTP 200 response with configurable body.
    """

    TOOL_NAME: ClassVar[str] = "APICall"
    IS_STUB: ClassVar[bool] = True
    DEFAULT_TIMEOUT: ClassVar[float] = 30.0

    def validate_config(self) -> None:
        pass  # Stubs accept any configuration

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        url = query.strip()
        method = kwargs.get("method", "GET")
        headers = kwargs.get("headers", {})

        return ToolResult(
            success=True,
            data={
                "status_code": 200,
                "body": {
                    "message": "Simulated API response",
                    "url": url,
                    "method": method,
                },
                "headers": {
                    "Content-Type": "application/json",
                    "X-Stub": "true",
                },
            },
            metadata={
                "is_stub": True,
                "url": url,
                "method": method,
                "request_headers": headers,
                "warning": f"Simulated API call to '{url}'",
            },
        )
