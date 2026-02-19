"""
AXON Standard Library — Tool Runtime Executors
================================================
Stub and real implementations for built-in tools.

Only ``Calculator`` and ``DateTimeTool`` have full implementations
(pure Python, no external dependencies). All other tools raise
``NotImplementedError`` — real integrations are planned for Phase 5.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════
#  IMPLEMENTED EXECUTORS
# ═══════════════════════════════════════════════════════════════════


def calculator_execute(expression: str) -> str:
    """Safely evaluate a mathematical expression.

    Supports: +, -, *, /, **, %, sqrt, abs, round, pi, e
    Rejects: imports, builtins, dunder attributes.

    Args:
        expression: A mathematical expression string.

    Returns:
        The result as a string.

    Raises:
        ValueError: If the expression is unsafe or invalid.
    """
    # Security: reject dangerous patterns
    forbidden = [
        "import", "__", "exec", "eval", "open",
        "os.", "sys.", "subprocess", "compile",
    ]
    expr_lower = expression.lower().strip()
    for pattern in forbidden:
        if pattern in expr_lower:
            raise ValueError(
                f"Unsafe expression: '{pattern}' is not allowed."
            )

    # Allow only safe math operations
    safe_ns: dict[str, object] = {
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
        "pi": math.pi,
        "e": math.e,
        "log": math.log,
        "log10": math.log10,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "ceil": math.ceil,
        "floor": math.floor,
        "pow": pow,
        "min": min,
        "max": max,
    }

    try:
        # Compile to check for syntax errors before eval
        code = compile(expression, "<calculator>", "eval")

        # Verify only allowed names are used
        for name in code.co_names:
            if name not in safe_ns:
                raise ValueError(
                    f"Unknown function '{name}'. "
                    f"Available: {', '.join(sorted(safe_ns.keys()))}"
                )

        result = eval(code, {"__builtins__": {}}, safe_ns)  # noqa: S307
        return str(result)
    except (SyntaxError, TypeError, ZeroDivisionError) as exc:
        raise ValueError(f"Invalid expression: {exc}") from exc


def datetime_execute(query: str) -> str:
    """Answer date/time queries.

    Supported queries:
    - "now" / "current" — current UTC datetime
    - "today" — today's date
    - "timestamp" — current UNIX timestamp

    Args:
        query: A date/time query string.

    Returns:
        The result as a string.
    """
    q = query.lower().strip()
    now = datetime.now(timezone.utc)

    if q in ("now", "current", "current_time"):
        return now.isoformat()
    elif q in ("today", "date", "current_date"):
        return now.date().isoformat()
    elif q in ("timestamp", "unix", "epoch"):
        return str(int(now.timestamp()))
    elif q in ("year",):
        return str(now.year)
    elif q in ("month",):
        return str(now.month)
    elif q in ("day",):
        return str(now.day)
    elif q in ("weekday", "day_of_week"):
        return now.strftime("%A")
    elif q in ("iso", "iso8601"):
        return now.isoformat()
    else:
        return (
            f"Current UTC: {now.isoformat()}, "
            f"Timestamp: {int(now.timestamp())}, "
            f"Date: {now.date().isoformat()}"
        )
