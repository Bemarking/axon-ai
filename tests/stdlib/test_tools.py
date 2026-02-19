"""
Tests for AXON Standard Library — Tool Definitions & Executors
================================================================
"""

from __future__ import annotations

import pytest

from axon.compiler.ir_nodes import IRToolSpec
from axon.stdlib.tools.definitions import (
    ALL_TOOLS,
    APICall,
    Calculator,
    CodeExecutor,
    DateTimeTool,
    FileReader,
    ImageAnalyzer,
    PDFExtractor,
    WebSearch,
)
from axon.stdlib.tools.executors import calculator_execute, datetime_execute


class TestToolDefinitions:
    """Verify all 8 tools have correct IR structure."""

    def test_count(self):
        assert len(ALL_TOOLS) == 8

    def test_unique_names(self):
        names = [t.name for t in ALL_TOOLS]
        assert len(names) == len(set(names))

    @pytest.mark.parametrize(
        "tool",
        ALL_TOOLS,
        ids=[t.name for t in ALL_TOOLS],
    )
    def test_ir_type(self, tool):
        assert isinstance(tool.ir, IRToolSpec)

    @pytest.mark.parametrize(
        "tool",
        ALL_TOOLS,
        ids=[t.name for t in ALL_TOOLS],
    )
    def test_has_description(self, tool):
        assert tool.description != ""


class TestImplementedTools:
    """Test Calculator and DateTimeTool have actual executors."""

    def test_calculator_has_executor(self):
        assert Calculator.executor_fn is not None

    def test_datetime_has_executor(self):
        assert DateTimeTool.executor_fn is not None


class TestStubTools:
    """Test that stub tools raise NotImplementedError."""

    @pytest.mark.asyncio
    async def test_websearch_raises(self):
        with pytest.raises(NotImplementedError, match="not implemented"):
            await WebSearch.execute("test query")

    @pytest.mark.asyncio
    async def test_code_executor_raises(self):
        with pytest.raises(NotImplementedError):
            await CodeExecutor.execute("print('hello')")

    @pytest.mark.asyncio
    async def test_file_reader_raises(self):
        with pytest.raises(NotImplementedError):
            await FileReader.execute("/path/to/file")

    @pytest.mark.asyncio
    async def test_pdf_extractor_raises(self):
        with pytest.raises(NotImplementedError):
            await PDFExtractor.execute("doc.pdf")

    @pytest.mark.asyncio
    async def test_image_analyzer_raises(self):
        with pytest.raises(NotImplementedError):
            await ImageAnalyzer.execute("image.png")

    @pytest.mark.asyncio
    async def test_api_call_raises(self):
        with pytest.raises(NotImplementedError):
            await APICall.execute("https://api.example.com")


# ═══════════════════════════════════════════════════════════════════
#  CALCULATOR EXECUTOR TESTS
# ═══════════════════════════════════════════════════════════════════


class TestCalculatorExecutor:
    def test_basic_addition(self):
        assert calculator_execute("2 + 3") == "5"

    def test_multiplication(self):
        assert calculator_execute("7 * 8") == "56"

    def test_division(self):
        assert calculator_execute("10 / 4") == "2.5"

    def test_power(self):
        assert calculator_execute("2 ** 10") == "1024"

    def test_modulo(self):
        assert calculator_execute("17 % 5") == "2"

    def test_sqrt(self):
        assert calculator_execute("sqrt(144)") == "12.0"

    def test_pi(self):
        result = float(calculator_execute("pi"))
        assert abs(result - 3.14159) < 0.001

    def test_complex_expression(self):
        result = float(calculator_execute("sqrt(9) + 2 ** 3"))
        assert result == 11.0

    def test_zero_division_raises(self):
        with pytest.raises(ValueError, match="Invalid expression"):
            calculator_execute("1/0")

    def test_import_blocked(self):
        with pytest.raises(ValueError, match="Unsafe"):
            calculator_execute("import os")

    def test_dunder_blocked(self):
        with pytest.raises(ValueError, match="Unsafe"):
            calculator_execute("__import__('os')")

    def test_exec_blocked(self):
        with pytest.raises(ValueError, match="Unsafe"):
            calculator_execute("exec('print(1)')")

    def test_unknown_function_blocked(self):
        with pytest.raises(ValueError, match="Unknown function"):
            calculator_execute("foobar(42)")

    def test_syntax_error(self):
        with pytest.raises(ValueError, match="Invalid expression"):
            calculator_execute("2 +* 3")


# ═══════════════════════════════════════════════════════════════════
#  DATETIME EXECUTOR TESTS
# ═══════════════════════════════════════════════════════════════════


class TestDateTimeExecutor:
    def test_now(self):
        result = datetime_execute("now")
        assert "T" in result  # ISO format
        assert "+" in result or "Z" in result  # timezone

    def test_today(self):
        result = datetime_execute("today")
        assert "-" in result
        assert "T" not in result  # date only

    def test_timestamp(self):
        result = datetime_execute("timestamp")
        assert result.isdigit()

    def test_year(self):
        result = datetime_execute("year")
        assert int(result) >= 2024

    def test_weekday(self):
        result = datetime_execute("weekday")
        days = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday",
        ]
        assert result in days

    def test_fallback(self):
        result = datetime_execute("something unknown")
        assert "UTC" in result
        assert "Timestamp" in result


# ═══════════════════════════════════════════════════════════════════
#  TOOL METADATA TESTS
# ═══════════════════════════════════════════════════════════════════


class TestToolMetadata:
    def test_websearch_requires_api_key(self):
        assert WebSearch.requires_api_key is True

    def test_calculator_no_api_key(self):
        assert Calculator.requires_api_key is False

    def test_code_executor_sandboxed(self):
        assert CodeExecutor.ir.sandbox is True

    def test_calculator_sandboxed(self):
        assert Calculator.ir.sandbox is True

    def test_websearch_has_provider(self):
        assert WebSearch.ir.provider == "brave"

    def test_websearch_max_results(self):
        assert WebSearch.ir.max_results == 5
