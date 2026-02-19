"""ImageAnalyzer stub — simulates vision-based image analysis."""

from __future__ import annotations

from typing import Any, ClassVar

from axon.runtime.tools.base_tool import BaseTool, ToolResult


class ImageAnalyzerStub(BaseTool):
    """STUB: Simulates image analysis / vision capabilities.

    Returns fake labels, description, and confidence scores.
    """

    TOOL_NAME: ClassVar[str] = "ImageAnalyzer"
    IS_STUB: ClassVar[bool] = True
    DEFAULT_TIMEOUT: ClassVar[float] = 20.0

    def validate_config(self) -> None:
        pass  # Stubs accept any configuration

    async def execute(self, query: str, **kwargs: Any) -> ToolResult:
        image_path = query.strip()
        detail_level = kwargs.get("detail", "standard")

        return ToolResult(
            success=True,
            data={
                "description": (
                    f"A simulated analysis of the image at '{image_path}'. "
                    "The image appears to contain objects of interest."
                ),
                "labels": [
                    {"label": "object", "confidence": 0.95},
                    {"label": "scene", "confidence": 0.88},
                    {"label": "text", "confidence": 0.72},
                ],
                "dimensions": {"width": 1920, "height": 1080},
                "format": "JPEG",
                "path": image_path,
            },
            metadata={
                "is_stub": True,
                "detail_level": detail_level,
                "warning": f"Simulated image analysis for '{image_path}'",
            },
        )
