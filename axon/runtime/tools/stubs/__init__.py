"""
AXON Runtime — Tool Stubs (Phase 4)
=====================================
Simulated tool implementations for development and testing.

Each stub inherits from ``BaseTool``, sets ``IS_STUB = True``,
and returns fake-but-realistic data.  Calculator and DateTimeTool
are *real* implementations (``IS_STUB = False``).

Call ``register_all_stubs(registry)`` to load everything at once.
"""

from __future__ import annotations

from axon.runtime.tools.registry import RuntimeToolRegistry


def register_all_stubs(registry: RuntimeToolRegistry) -> None:
    """Register all Phase 4 tool implementations into *registry*."""
    from axon.runtime.tools.stubs.api_call_stub import APICallStub
    from axon.runtime.tools.stubs.calculator_tool import CalculatorTool
    from axon.runtime.tools.stubs.code_executor_stub import CodeExecutorStub
    from axon.runtime.tools.stubs.datetime_tool import DateTimeTool
    from axon.runtime.tools.stubs.file_reader_stub import FileReaderStub
    from axon.runtime.tools.stubs.image_analyzer_stub import ImageAnalyzerStub
    from axon.runtime.tools.stubs.pdf_extractor_stub import PDFExtractorStub
    from axon.runtime.tools.stubs.web_search_stub import WebSearchStub

    for cls in (
        WebSearchStub,
        CodeExecutorStub,
        FileReaderStub,
        PDFExtractorStub,
        ImageAnalyzerStub,
        CalculatorTool,
        DateTimeTool,
        APICallStub,
    ):
        registry.register(cls)
