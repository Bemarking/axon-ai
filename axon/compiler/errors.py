"""
AXON Compiler — Error Hierarchy
================================
All compile-time errors for the AXON language.

Hierarchy:
  AxonError
  ├── AxonLexerError   — bad character, unterminated string
  ├── AxonParseError   — unexpected token, missing delimiter
  └── AxonTypeError    — semantic type violation
"""

from __future__ import annotations
from dataclasses import dataclass, field


class AxonError(Exception):
    """Base error for all AXON compile-time errors."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.line = line
        self.column = column
        self.message = message
        super().__init__(self._format())

    def _format(self) -> str:
        location = f"[line {self.line}, col {self.column}]" if self.line else ""
        return f"{self.__class__.__name__} {location}: {self.message}"


class AxonLexerError(AxonError):
    """Raised when the lexer encounters invalid input."""
    pass


class AxonParseError(AxonError):
    """Raised when the parser encounters unexpected tokens."""

    def __init__(
        self,
        message: str,
        line: int = 0,
        column: int = 0,
        expected: str | None = None,
        found: str | None = None,
    ):
        self.expected = expected
        self.found = found
        if expected and found:
            message = f"{message} (expected {expected}, found {found})"
        super().__init__(message, line, column)


@dataclass
class TypeErrorInfo:
    """Structured info for a single type-checking violation."""
    message: str
    line: int = 0
    column: int = 0
    severity: str = "error"  # "error" | "warning"
    code: str = ""  # e.g. "AXON_T001"


class AxonTypeError(AxonError):
    """Raised when semantic type validation fails."""

    def __init__(
        self,
        message: str,
        line: int = 0,
        column: int = 0,
        errors: list[TypeErrorInfo] | None = None,
    ):
        self.errors = errors or []
        super().__init__(message, line, column)
