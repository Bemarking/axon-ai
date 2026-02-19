"""PDFExtractor stub — simulates PDF text extraction."""

from __future__ import annotations

from typing import Any, ClassVar

from axon.runtime.tools.base_tool import BaseTool, ToolResult


class PDFExtractorStub(BaseTool):
    """STUB: Simulates extracting text and metadata from a PDF.

    Returns fake extracted text with page-level information.
    """

    TOOL_NAME: ClassVar[str] = "PDFExtractor"
    IS_STUB: ClassVar[bool] = True
    DEFAULT_TIMEOUT: ClassVar[float] = 15.0

    def validate_config(self) -> None:
        pass  # Stubs accept any configuration

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        path = query.strip()
        pages_requested = kwargs.get("pages", None)

        # Simulate a 3-page document
        all_pages = [
            {
                "page": 1,
                "text": (
                    f"Simulated PDF content from '{path}', page 1. "
                    "Introduction and abstract of the document."
                ),
            },
            {
                "page": 2,
                "text": (
                    "Main body of the simulated PDF. "
                    "Contains detailed analysis and data."
                ),
            },
            {
                "page": 3,
                "text": (
                    "Conclusion and references. "
                    "Summary of key findings from the document."
                ),
            },
        ]

        if pages_requested is not None:
            pages = [p for p in all_pages if p["page"] in pages_requested]
        else:
            pages = all_pages

        full_text = "\n\n".join(p["text"] for p in pages)

        return ToolResult(
            success=True,
            data={
                "text": full_text,
                "pages": pages,
                "total_pages": len(all_pages),
                "path": path,
            },
            metadata={
                "is_stub": True,
                "warning": f"Simulated PDF extraction for '{path}'",
            },
        )
