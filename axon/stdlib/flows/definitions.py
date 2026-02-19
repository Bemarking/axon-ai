"""
AXON Standard Library — Flow Definitions
==========================================
All 8 built-in flows from the AXON spec §8.2.

Each flow is a multi-step ``IRFlow`` wrapped in ``StdlibFlow``
with metadata (description, category, version).

Flows available::

    Summarize          — Condense any document
    ExtractEntities    — Named entity recognition
    CompareDocuments   — Side-by-side analysis
    TranslateDocument  — Language translation
    FactCheck          — Claim verification
    SentimentAnalysis  — Tone and sentiment
    ClassifyContent    — Category labeling
    GenerateReport     — Structured report from data
"""

from __future__ import annotations

from axon.compiler.ir_nodes import (
    IRFlow,
    IRParameter,
    IRProbe,
    IRReason,
    IRStep,
    IRWeave,
)
from axon.stdlib.base import StdlibFlow


# ═══════════════════════════════════════════════════════════════════
#  HELPER — build a named step with a sub-operation
# ═══════════════════════════════════════════════════════════════════


def _step(
    name: str,
    output_type: str,
    *,
    ask: str = "",
    probe: IRProbe | None = None,
    reason: IRReason | None = None,
    weave: IRWeave | None = None,
    given: str = "",
) -> IRStep:
    """Shorthand for building an IRStep with one sub-operation."""
    return IRStep(
        name=name,
        output_type=output_type,
        ask=ask,
        probe=probe,
        reason=reason,
        weave=weave,
        given=given,
    )


# ═══════════════════════════════════════════════════════════════════
#  FLOW DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

Summarize = StdlibFlow(
    ir=IRFlow(
        name="Summarize",
        parameters=(
            IRParameter(name="doc", type_name="Document"),
        ),
        return_type_name="Summary",
        steps=(
            _step(
                "Extract",
                "EntityMap",
                probe=IRProbe(
                    target="doc",
                    fields=(
                        "key_points", "main_themes", "conclusions",
                        "supporting_evidence",
                    ),
                ),
            ),
            _step(
                "Condense",
                "Summary",
                reason=IRReason(
                    name="Condensation",
                    given=("Extract",),
                    depth=2,
                    ask="Distill the key points into a concise summary "
                        "preserving the most important information.",
                    output_type="Summary",
                ),
            ),
        ),
    ),
    description="Condense any document into a concise summary.",
    category="analysis",
)

ExtractEntities = StdlibFlow(
    ir=IRFlow(
        name="ExtractEntities",
        parameters=(
            IRParameter(name="doc", type_name="Document"),
        ),
        return_type_name="EntityMap",
        steps=(
            _step(
                "Identify",
                "EntityMap",
                probe=IRProbe(
                    target="doc",
                    fields=(
                        "persons", "organizations", "locations",
                        "dates", "monetary_values", "events",
                    ),
                ),
            ),
            _step(
                "Classify",
                "EntityMap",
                reason=IRReason(
                    name="Classification",
                    given=("Identify",),
                    depth=1,
                    ask="Classify each entity by type and resolve "
                        "co-references to canonical names.",
                    output_type="EntityMap",
                ),
            ),
        ),
    ),
    description="Extract and classify named entities from a document.",
    category="extraction",
)

CompareDocuments = StdlibFlow(
    ir=IRFlow(
        name="CompareDocuments",
        parameters=(
            IRParameter(name="doc_a", type_name="Document"),
            IRParameter(name="doc_b", type_name="Document"),
        ),
        return_type_name="StructuredReport",
        steps=(
            _step(
                "ExtractA",
                "EntityMap",
                probe=IRProbe(
                    target="doc_a",
                    fields=(
                        "key_claims", "structure", "conclusions",
                        "methodology",
                    ),
                ),
            ),
            _step(
                "ExtractB",
                "EntityMap",
                probe=IRProbe(
                    target="doc_b",
                    fields=(
                        "key_claims", "structure", "conclusions",
                        "methodology",
                    ),
                ),
            ),
            _step(
                "Analyze",
                "ReasoningChain",
                reason=IRReason(
                    name="Comparison",
                    given=("ExtractA", "ExtractB"),
                    depth=3,
                    show_work=True,
                    ask="Compare the two documents. Identify agreements, "
                        "contradictions, gaps, and unique contributions.",
                    output_type="ReasoningChain",
                ),
            ),
            _step(
                "Synthesize",
                "StructuredReport",
                weave=IRWeave(
                    sources=("ExtractA", "ExtractB", "Analyze"),
                    target="ComparisonReport",
                    format_type="StructuredReport",
                    priority=(
                        "contradictions", "agreements",
                        "unique_contributions", "gaps",
                    ),
                ),
            ),
        ),
    ),
    description="Compare two documents side-by-side with detailed analysis.",
    category="analysis",
)

TranslateDocument = StdlibFlow(
    ir=IRFlow(
        name="TranslateDocument",
        parameters=(
            IRParameter(name="doc", type_name="Document"),
            IRParameter(name="target_lang", type_name="String"),
        ),
        return_type_name="Translation",
        steps=(
            _step(
                "Analyze",
                "EntityMap",
                probe=IRProbe(
                    target="doc",
                    fields=(
                        "language", "tone", "technical_terms",
                        "idiomatic_expressions", "cultural_references",
                    ),
                ),
            ),
            _step(
                "Translate",
                "Translation",
                reason=IRReason(
                    name="Translation",
                    given=("Analyze",),
                    depth=2,
                    ask="Translate the document preserving tone, "
                        "technical accuracy, and cultural nuances.",
                    output_type="Translation",
                ),
            ),
        ),
    ),
    description="Translate a document with cultural context preservation.",
    category="translation",
)

FactCheck = StdlibFlow(
    ir=IRFlow(
        name="FactCheck",
        parameters=(
            IRParameter(name="claims", type_name="Document"),
        ),
        return_type_name="StructuredReport",
        steps=(
            _step(
                "ExtractClaims",
                "EntityMap",
                probe=IRProbe(
                    target="claims",
                    fields=(
                        "factual_claims", "citations", "statistics",
                        "dates", "named_entities",
                    ),
                ),
            ),
            _step(
                "Verify",
                "ReasoningChain",
                reason=IRReason(
                    name="Verification",
                    given=("ExtractClaims",),
                    depth=3,
                    show_work=True,
                    ask="For each claim, assess: Is it verifiable? "
                        "Is the cited source reliable? Does the "
                        "evidence support the claim?",
                    output_type="ReasoningChain",
                ),
            ),
            _step(
                "Report",
                "StructuredReport",
                weave=IRWeave(
                    sources=("ExtractClaims", "Verify"),
                    target="FactCheckReport",
                    format_type="StructuredReport",
                    priority=(
                        "false_claims", "unverifiable_claims",
                        "verified_claims", "partially_true",
                    ),
                ),
            ),
        ),
    ),
    description="Verify factual claims with sourced evidence.",
    category="verification",
)

SentimentAnalysis = StdlibFlow(
    ir=IRFlow(
        name="SentimentAnalysis",
        parameters=(
            IRParameter(name="doc", type_name="Document"),
        ),
        return_type_name="SentimentScore",
        steps=(
            _step(
                "Extract",
                "EntityMap",
                probe=IRProbe(
                    target="doc",
                    fields=(
                        "emotional_tone", "sentiment_markers",
                        "intensity_signals", "context_modifiers",
                    ),
                ),
            ),
            _step(
                "Analyze",
                "SentimentScore",
                reason=IRReason(
                    name="SentimentScoring",
                    given=("Extract",),
                    depth=2,
                    ask="Score the overall sentiment from -1 (very negative) "
                        "to +1 (very positive). Account for sarcasm, "
                        "irony, and context.",
                    output_type="SentimentScore",
                ),
            ),
        ),
    ),
    description="Analyze tone and sentiment with nuanced scoring.",
    category="analysis",
)

ClassifyContent = StdlibFlow(
    ir=IRFlow(
        name="ClassifyContent",
        parameters=(
            IRParameter(name="doc", type_name="Document"),
            IRParameter(name="categories", type_name="String"),
        ),
        return_type_name="EntityMap",
        steps=(
            _step(
                "Extract",
                "EntityMap",
                probe=IRProbe(
                    target="doc",
                    fields=(
                        "topics", "keywords", "themes",
                        "domain_signals",
                    ),
                ),
            ),
            _step(
                "Classify",
                "EntityMap",
                reason=IRReason(
                    name="Classification",
                    given=("Extract",),
                    depth=2,
                    ask="Classify the content into the provided categories "
                        "with confidence scores for each category.",
                    output_type="EntityMap",
                ),
            ),
        ),
    ),
    description="Classify content into user-defined categories.",
    category="classification",
)

GenerateReport = StdlibFlow(
    ir=IRFlow(
        name="GenerateReport",
        parameters=(
            IRParameter(name="data", type_name="Document"),
        ),
        return_type_name="StructuredReport",
        steps=(
            _step(
                "Extract",
                "EntityMap",
                probe=IRProbe(
                    target="data",
                    fields=(
                        "key_metrics", "trends", "anomalies",
                        "comparisons", "conclusions",
                    ),
                ),
            ),
            _step(
                "Analyze",
                "ReasoningChain",
                reason=IRReason(
                    name="Analysis",
                    given=("Extract",),
                    depth=3,
                    show_work=True,
                    ask="Analyze the data to identify patterns, draw "
                        "conclusions, and formulate recommendations.",
                    output_type="ReasoningChain",
                ),
            ),
            _step(
                "Synthesize",
                "StructuredReport",
                weave=IRWeave(
                    sources=("Extract", "Analyze"),
                    target="FinalReport",
                    format_type="StructuredReport",
                    priority=(
                        "executive_summary", "key_findings",
                        "recommendations", "detailed_analysis",
                    ),
                ),
            ),
        ),
    ),
    description="Generate a structured report from raw data.",
    category="reporting",
)


# ── Canonical list for registration ──────────────────────────────

ALL_FLOWS: tuple[StdlibFlow, ...] = (
    Summarize,
    ExtractEntities,
    CompareDocuments,
    TranslateDocument,
    FactCheck,
    SentimentAnalysis,
    ClassifyContent,
    GenerateReport,
)
