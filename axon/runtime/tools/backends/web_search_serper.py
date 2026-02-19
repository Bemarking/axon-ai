"""
AXON Runtime — WebSearch Backend (Serper.dev)
==============================================
Real web search using Serper.dev's Google Search API wrapper.

Get API key: https://serper.dev/
Free tier: 2 500 queries (one-time).
Paid: $50/month for 100 000 queries.

Configuration keys (via ``config`` dict or ``SERPER_API_KEY`` env var):

* ``api_key``  — Serper API key (**required**).
* ``gl``       — Country code for results (default: ``"us"``).
* ``hl``       — Language code (default: ``"en"``).
* ``timeout``  — HTTP timeout in seconds (default: ``10``).
"""

from __future__ import annotations

import logging
import os
from typing import Any, ClassVar

import httpx

from axon.runtime.tools.base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# ── Serper endpoint ──────────────────────────────────────────
_SERPER_ENDPOINT = "https://google.serper.dev/search"


class WebSearchSerper(BaseTool):
    """Real web search via Serper.dev (Google Search API).

    Returns a list of organic results, each containing
    ``title``, ``url``, ``snippet``, ``source``, and ``position``.

    Example::

        tool = WebSearchSerper({"api_key": "..."})
        result = await tool.execute("Python 3.13 features", max_results=5)
        for item in result.data:
            print(item["title"], item["url"])
    """

    TOOL_NAME: ClassVar[str] = "WebSearch"
    IS_STUB: ClassVar[bool] = False
    DEFAULT_TIMEOUT: ClassVar[float] = 15.0

    # ── Lifecycle ────────────────────────────────────────────

    def validate_config(self) -> None:
        """Ensure an API key is available (config dict or env var)."""
        if "api_key" not in self.config:
            env_key = os.getenv("SERPER_API_KEY")
            if env_key:
                self.config["api_key"] = env_key
            else:
                raise ValueError(
                    "WebSearchSerper requires 'api_key' in config or "
                    "SERPER_API_KEY environment variable. "
                    "Get one at: https://serper.dev/"
                )

    # ── Execution ────────────────────────────────────────────

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        """Search the web via Serper.dev.

        Args:
            query:        The search query string.
            max_results:  Number of results to return (default ``5``).

        Returns:
            ``ToolResult`` with ``data`` as a list of result dicts.
        """
        max_results = min(kwargs.get("max_results", 5), 20)
        timeout = self.config.get("timeout", 10)

        payload: dict[str, Any] = {
            "q": query,
            "num": max_results,
            "gl": self.config.get("gl", "us"),
            "hl": self.config.get("hl", "en"),
        }

        headers = {
            "X-API-KEY": self.config["api_key"],
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    _SERPER_ENDPOINT,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                )
                response.raise_for_status()

            data = response.json()
            organic = data.get("organic", [])

            results = [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("displayedLink", ""),
                    "position": item.get("position", 0),
                }
                for item in organic[:max_results]
            ]

            return ToolResult(
                success=True,
                data=results,
                metadata={
                    "query": query,
                    "is_stub": False,
                    "provider": "serper",
                    "total_results": len(results),
                    "search_time": (
                        data.get("searchParameters", {}).get("time")
                    ),
                },
            )

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            detail = _status_detail(status)
            logger.error(
                "Serper API HTTP %d for query '%s': %s",
                status, query, detail,
            )
            return ToolResult(
                success=False,
                data=None,
                error=f"Serper API HTTP {status}: {detail}",
                metadata={
                    "query": query,
                    "status_code": status,
                },
            )

        except httpx.TimeoutException:
            logger.warning(
                "Serper API timeout (%ds) for query '%s'",
                timeout, query,
            )
            return ToolResult(
                success=False,
                data=None,
                error=f"Request timed out after {timeout}s",
                metadata={"query": query},
            )

        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected Serper error for '%s'", query)
            return ToolResult(
                success=False,
                data=None,
                error=f"Unexpected error: {exc}",
                metadata={
                    "query": query,
                    "exception_type": type(exc).__name__,
                },
            )


# ── Helpers ──────────────────────────────────────────────────


def _status_detail(code: int) -> str:
    """Human-readable detail for common HTTP status codes."""
    return {
        401: "Invalid API key",
        403: "Access denied — check your Serper plan",
        429: "Rate limit exceeded — wait or upgrade plan",
        500: "Serper internal error — try again later",
    }.get(code, "Unknown error")
