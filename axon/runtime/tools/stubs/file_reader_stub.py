"""FileReader stub — simulates file reading."""

from __future__ import annotations

from typing import Any, ClassVar

from axon.runtime.tools.base_tool import BaseTool, ToolResult


class FileReaderStub(BaseTool):
    """STUB: Simulates reading a local or remote file.

    Returns fake content based on the file path extension.
    """

    TOOL_NAME: ClassVar[str] = "FileReader"
    IS_STUB: ClassVar[bool] = True
    DEFAULT_TIMEOUT: ClassVar[float] = 5.0

    def validate_config(self) -> None:
        pass  # Stubs accept any configuration

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        path = query.strip()
        encoding = kwargs.get("encoding", "utf-8")

        # Simulate content based on extension
        if path.endswith((".json", ".jsonl")):
            content = '{"key": "simulated_value", "items": [1, 2, 3]}'
            mime = "application/json"
        elif path.endswith((".csv", ".tsv")):
            content = "col_a,col_b,col_c\nval1,val2,val3\nval4,val5,val6"
            mime = "text/csv"
        elif path.endswith((".md", ".markdown")):
            content = f"# Simulated Markdown\n\nContent from `{path}`."
            mime = "text/markdown"
        elif path.endswith((".html", ".htm")):
            content = f"<html><body><p>Simulated HTML from {path}</p></body></html>"
            mime = "text/html"
        else:
            content = f"Simulated plain text content from: {path}"
            mime = "text/plain"

        return ToolResult(
            success=True,
            data={
                "content": content,
                "path": path,
                "encoding": encoding,
                "mime_type": mime,
                "size_bytes": len(content),
            },
            metadata={
                "is_stub": True,
                "warning": f"Simulated file read for '{path}'",
            },
        )
