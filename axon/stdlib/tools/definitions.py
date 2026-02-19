"""
AXON Standard Library — Tool Definitions
==========================================
All 8 built-in tools from the AXON spec §8.4.

Each tool is an ``IRToolSpec`` wrapped in ``StdlibTool``
with executor function and metadata.

Tools available::

    WebSearch       — Live web search (stub)
    CodeExecutor    — Safe code execution sandbox (stub)
    FileReader      — Local/remote file reading (stub)
    PDFExtractor    — PDF text + structure extraction (stub)
    ImageAnalyzer   — Vision capabilities (stub)
    Calculator      — Precise arithmetic (✅ implemented)
    DateTimeTool    — Temporal reasoning (✅ implemented)
    APICall         — Generic REST API caller (stub)
"""

from __future__ import annotations

from axon.compiler.ir_nodes import IRToolSpec
from axon.stdlib.base import StdlibTool
from axon.stdlib.tools.executors import calculator_execute, datetime_execute


# ═══════════════════════════════════════════════════════════════════
#  TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

WebSearch = StdlibTool(
    ir=IRToolSpec(
        name="WebSearch",
        provider="brave",
        max_results=5,
        filter_expr="recent(days: 30)",
        timeout="10s",
        sandbox=False,
    ),
    executor_fn=None,  # Stub — real integration in Phase 5
    description="Live web search via Brave Search API.",
    requires_api_key=True,
)

CodeExecutor = StdlibTool(
    ir=IRToolSpec(
        name="CodeExecutor",
        timeout="30s",
        runtime="python",
        sandbox=True,
    ),
    executor_fn=None,  # Stub — real integration in Phase 5
    description="Safe sandboxed code execution environment.",
    requires_api_key=False,
)

FileReader = StdlibTool(
    ir=IRToolSpec(
        name="FileReader",
        timeout="5s",
        sandbox=False,
    ),
    executor_fn=None,  # Stub — real integration in Phase 5
    description="Read local or remote files.",
    requires_api_key=False,
)

PDFExtractor = StdlibTool(
    ir=IRToolSpec(
        name="PDFExtractor",
        timeout="15s",
        sandbox=False,
    ),
    executor_fn=None,  # Stub — real integration in Phase 5
    description="Extract text and structure from PDF documents.",
    requires_api_key=False,
)

ImageAnalyzer = StdlibTool(
    ir=IRToolSpec(
        name="ImageAnalyzer",
        timeout="20s",
        sandbox=False,
    ),
    executor_fn=None,  # Stub — real integration in Phase 5
    description="Analyze images using vision model capabilities.",
    requires_api_key=True,
)

Calculator = StdlibTool(
    ir=IRToolSpec(
        name="Calculator",
        timeout="2s",
        sandbox=True,
    ),
    executor_fn=calculator_execute,
    description="Precise arithmetic with safe expression evaluation.",
    requires_api_key=False,
)

DateTimeTool = StdlibTool(
    ir=IRToolSpec(
        name="DateTimeTool",
        timeout="1s",
        sandbox=True,
    ),
    executor_fn=datetime_execute,
    description="Temporal reasoning — current date, time, timestamps.",
    requires_api_key=False,
)

APICall = StdlibTool(
    ir=IRToolSpec(
        name="APICall",
        timeout="30s",
        sandbox=False,
    ),
    executor_fn=None,  # Stub — real integration in Phase 5
    description="Generic REST API caller for external service integration.",
    requires_api_key=True,
)


# ── Canonical list for registration ──────────────────────────────

ALL_TOOLS: tuple[StdlibTool, ...] = (
    WebSearch,
    CodeExecutor,
    FileReader,
    PDFExtractor,
    ImageAnalyzer,
    Calculator,
    DateTimeTool,
    APICall,
)
