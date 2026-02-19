"""
Tests for AXON Standard Library — Flow Definitions
====================================================
"""

from __future__ import annotations

import pytest

from axon.compiler.ir_nodes import IRFlow, IRStep
from axon.stdlib.flows.definitions import (
    ALL_FLOWS,
    ClassifyContent,
    CompareDocuments,
    ExtractEntities,
    FactCheck,
    GenerateReport,
    SentimentAnalysis,
    Summarize,
    TranslateDocument,
)


class TestFlowDefinitions:
    """Verify all 8 flows have correct IR structure."""

    def test_count(self):
        assert len(ALL_FLOWS) == 8

    def test_unique_names(self):
        names = [f.name for f in ALL_FLOWS]
        assert len(names) == len(set(names))

    @pytest.mark.parametrize(
        "flow",
        ALL_FLOWS,
        ids=[f.name for f in ALL_FLOWS],
    )
    def test_ir_type(self, flow):
        assert isinstance(flow.ir, IRFlow)

    @pytest.mark.parametrize(
        "flow",
        ALL_FLOWS,
        ids=[f.name for f in ALL_FLOWS],
    )
    def test_has_description(self, flow):
        assert flow.description != ""

    @pytest.mark.parametrize(
        "flow",
        ALL_FLOWS,
        ids=[f.name for f in ALL_FLOWS],
    )
    def test_has_steps(self, flow):
        """Each flow has at least 2 steps."""
        assert len(flow.ir.steps) >= 2

    @pytest.mark.parametrize(
        "flow",
        ALL_FLOWS,
        ids=[f.name for f in ALL_FLOWS],
    )
    def test_has_parameters(self, flow):
        """Each flow has at least 1 parameter."""
        assert len(flow.ir.parameters) >= 1

    @pytest.mark.parametrize(
        "flow",
        ALL_FLOWS,
        ids=[f.name for f in ALL_FLOWS],
    )
    def test_has_return_type(self, flow):
        """Each flow declares a return type."""
        assert flow.ir.return_type_name != ""

    @pytest.mark.parametrize(
        "flow",
        ALL_FLOWS,
        ids=[f.name for f in ALL_FLOWS],
    )
    def test_steps_are_irstep(self, flow):
        """All flow steps are IRStep nodes."""
        for step in flow.ir.steps:
            assert isinstance(step, IRStep)

    @pytest.mark.parametrize(
        "flow",
        ALL_FLOWS,
        ids=[f.name for f in ALL_FLOWS],
    )
    def test_step_names_unique(self, flow):
        """Step names within a flow are unique."""
        names = [s.name for s in flow.ir.steps]
        assert len(names) == len(set(names))


class TestSpecificFlows:
    """Spot-checks on key flow structures."""

    def test_summarize_has_probe_then_reason(self):
        steps = Summarize.ir.steps
        assert steps[0].probe is not None  # Extract step
        assert steps[1].reason is not None  # Condense step

    def test_compare_has_four_steps(self):
        assert len(CompareDocuments.ir.steps) == 4

    def test_compare_has_two_params(self):
        assert len(CompareDocuments.ir.parameters) == 2

    def test_compare_has_weave(self):
        # Last step should use weave
        last = CompareDocuments.ir.steps[-1]
        assert last.weave is not None

    def test_factcheck_has_three_steps(self):
        assert len(FactCheck.ir.steps) == 3

    def test_translate_has_target_lang_param(self):
        params = TranslateDocument.ir.parameters
        param_names = [p.name for p in params]
        assert "target_lang" in param_names

    def test_generate_report_has_weave(self):
        last = GenerateReport.ir.steps[-1]
        assert last.weave is not None

    def test_extract_entities_returns_entity_map(self):
        assert ExtractEntities.ir.return_type_name == "EntityMap"

    def test_sentiment_returns_sentiment_score(self):
        assert SentimentAnalysis.ir.return_type_name == "SentimentScore"

    def test_classify_has_categories_param(self):
        params = ClassifyContent.ir.parameters
        param_names = [p.name for p in params]
        assert "categories" in param_names
