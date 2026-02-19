"""
AXON Standard Library — Anchor Checker Functions
==================================================
Lightweight keyword-based enforcement for each built-in anchor.

Each checker receives the model's output text and returns
``(passed, violations)`` where ``violations`` is a list of
human-readable violation descriptions.

These are Phase 3-style keyword checkers. Full NLI-based
enforcement is planned for Phase 6.
"""

from __future__ import annotations

import re


def _find_keywords(
    content: str, keywords: list[str]
) -> list[str]:
    """Find which keywords appear in content (case-insensitive)."""
    lower = content.lower()
    return [kw for kw in keywords if kw.lower() in lower]


# ═══════════════════════════════════════════════════════════════════
#  CHECKER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════


def check_no_hallucination(content: str) -> tuple[bool, list[str]]:
    """Verify content doesn't contain hallucination indicators.

    Checks for:
    - Hedging without citations ("I believe", "probably", "might be")
    - Fabricated references
    - Unsubstantiated absolute claims
    """
    violations: list[str] = []
    lower = content.lower()

    # Hedging phrases that indicate uncertainty without evidence
    hedging = [
        "i believe", "i think", "probably", "might be",
        "could be", "it seems like", "supposedly",
        "i'm not sure but", "i'm guessing",
    ]
    found = _find_keywords(lower, hedging)
    if found:
        violations.append(
            f"Hedging without citation: {', '.join(found)}"
        )

    return len(violations) == 0, violations


def check_factual_only(content: str) -> tuple[bool, list[str]]:
    """Verify content sticks to factual claims, no opinions.

    Checks for opinion indicators unless explicitly declared.
    """
    violations: list[str] = []
    lower = content.lower()

    opinion_markers = [
        "in my opinion", "i feel that", "personally",
        "i prefer", "my favorite", "i'd recommend",
        "i suggest", "to me,",
    ]
    found = _find_keywords(lower, opinion_markers)
    if found:
        violations.append(
            f"Opinion markers detected: {', '.join(found)}"
        )

    return len(violations) == 0, violations


def check_safe_output(content: str) -> tuple[bool, list[str]]:
    """Verify content doesn't contain harmful material.

    Checks for violence, hate speech, and harmful instructions.
    """
    violations: list[str] = []
    lower = content.lower()

    harmful_patterns = [
        "how to make a bomb", "how to hack", "how to steal",
        "kill yourself", "self-harm", "suicide method",
        "racial slur", "hate speech",
    ]
    found = _find_keywords(lower, harmful_patterns)
    if found:
        violations.append(
            f"Harmful content detected: {', '.join(found)}"
        )

    return len(violations) == 0, violations


def check_privacy_guard(content: str) -> tuple[bool, list[str]]:
    """Verify content doesn't expose personally identifiable information.

    Checks for SSNs, phone numbers, email addresses, and credit cards.
    """
    violations: list[str] = []

    # SSN pattern (XXX-XX-XXXX)
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", content):
        violations.append("Possible SSN detected")

    # Credit card pattern (16 digits with optional separators)
    if re.search(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", content):
        violations.append("Possible credit card number detected")

    # Email in output (might be PII)
    if re.search(
        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        content,
    ):
        violations.append("Email address detected in output")

    # Phone numbers (various formats)
    if re.search(
        r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        content,
    ):
        violations.append("Phone number detected in output")

    return len(violations) == 0, violations


def check_no_bias(content: str) -> tuple[bool, list[str]]:
    """Verify content is politically and demographically neutral.

    Checks for explicit bias indicators and loaded language.
    """
    violations: list[str] = []
    lower = content.lower()

    bias_markers = [
        "the best political party", "the right wing is",
        "the left wing is", "liberals are", "conservatives are",
        "all men are", "all women are", "that race is",
    ]
    found = _find_keywords(lower, bias_markers)
    if found:
        violations.append(
            f"Potential bias detected: {', '.join(found)}"
        )

    return len(violations) == 0, violations


def check_child_safe(content: str) -> tuple[bool, list[str]]:
    """Verify content is appropriate for minors.

    Checks for adult content, violence, profanity, and drug references.
    """
    violations: list[str] = []
    lower = content.lower()

    inappropriate = [
        "explicit sexual", "pornography", "graphic violence",
        "drug use instructions", "alcohol abuse",
        "gambling tutorial",
    ]
    found = _find_keywords(lower, inappropriate)
    if found:
        violations.append(
            f"Age-inappropriate content detected: {', '.join(found)}"
        )

    # Basic profanity check (intentionally conservative)
    profanity = ["fuck", "shit", "damn", "bastard", "bitch", "ass "]
    found_profanity = _find_keywords(lower, profanity)
    if found_profanity:
        violations.append("Profanity detected")

    return len(violations) == 0, violations


def check_no_code_execution(content: str) -> tuple[bool, list[str]]:
    """Verify content doesn't attempt code execution or system commands.

    Checks for shell commands, file operations, and dangerous code.
    """
    violations: list[str] = []
    lower = content.lower()

    dangerous = [
        "os.system(", "subprocess.", "exec(", "eval(",
        "rm -rf", "del /f", "format c:",
        "import os", "import subprocess",
        "__import__(",
    ]
    found = _find_keywords(lower, dangerous)
    if found:
        violations.append(
            f"Code execution attempt detected: {', '.join(found)}"
        )

    return len(violations) == 0, violations


def check_audit_trail(content: str) -> tuple[bool, list[str]]:
    """Verify content includes reasoning trace.

    Checks that the output contains structured reasoning markers.
    """
    violations: list[str] = []
    lower = content.lower()

    # Must contain at least one reasoning indicator
    reasoning_markers = [
        "reasoning:", "therefore", "because", "based on",
        "evidence:", "conclusion:", "analysis:",
        "step 1", "firstly", "in summary",
    ]
    has_reasoning = any(m in lower for m in reasoning_markers)
    if not has_reasoning:
        violations.append(
            "No reasoning trace found. "
            "AuditTrail requires visible reasoning steps."
        )

    return len(violations) == 0, violations
