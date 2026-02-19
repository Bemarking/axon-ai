"""WebSearch stub — returns realistic-looking fake search results."""

from __future__ import annotations

from typing import Any, ClassVar

from axon.runtime.tools.base_tool import BaseTool, ToolResult


class WebSearchStub(BaseTool):
    """STUB: Simulates web search without making real API calls.

    Returns fake results that mimic the structure of a real
    search engine response (title, url, snippet, source, date).
    """

    TOOL_NAME: ClassVar[str] = "WebSearch"
    IS_STUB: ClassVar[bool] = True
    DEFAULT_TIMEOUT: ClassVar[float] = 10.0

    def validate_config(self) -> None:
        # Stubs accept any config
        pass

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        max_results = kwargs.get("max_results", 5)
        max_results = min(max_results, 10)

        results = [
            {
                "title": f"Result {i + 1} for: {query}",
                "url": f"https://example.com/search/{i + 1}",
                "snippet": (
                    f"This is a simulated search result about '{query}'. "
                    f"Contains relevant information from a trusted source."
                ),
                "source": "example.com",
                "published_date": "2026-02-01",
            }
            for i in range(max_results)
        ]

        return ToolResult(
            success=True,
            data=results,
            metadata={
                "query": query,
                "total_results": len(results),
                "is_stub": True,
                "warning": "Simulated data from WebSearchStub",
            },
        )
