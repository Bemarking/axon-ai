"""
Tests for AXON Standard Library — Persona Definitions
======================================================
"""

from __future__ import annotations

import pytest

from axon.compiler.ir_nodes import IRPersona
from axon.stdlib.personas.definitions import (
    ALL_PERSONAS,
    Analyst,
    Coder,
    Critic,
    LegalExpert,
    Researcher,
    Summarizer,
    Translator,
    Writer,
)


class TestPersonaDefinitions:
    """Verify all 8 personas have correct IR structure."""

    def test_count(self):
        """Exactly 8 personas in ALL_PERSONAS."""
        assert len(ALL_PERSONAS) == 8

    def test_unique_names(self):
        """All persona names are unique."""
        names = [p.name for p in ALL_PERSONAS]
        assert len(names) == len(set(names))

    @pytest.mark.parametrize(
        "persona",
        ALL_PERSONAS,
        ids=[p.name for p in ALL_PERSONAS],
    )
    def test_ir_type(self, persona):
        """Each persona wraps an IRPersona."""
        assert isinstance(persona.ir, IRPersona)

    @pytest.mark.parametrize(
        "persona",
        ALL_PERSONAS,
        ids=[p.name for p in ALL_PERSONAS],
    )
    def test_has_description(self, persona):
        """Each persona has a non-empty description."""
        assert persona.description != ""

    @pytest.mark.parametrize(
        "persona",
        ALL_PERSONAS,
        ids=[p.name for p in ALL_PERSONAS],
    )
    def test_ir_has_domain(self, persona):
        """Each persona IR has at least one domain."""
        assert len(persona.ir.domain) >= 1

    @pytest.mark.parametrize(
        "persona",
        ALL_PERSONAS,
        ids=[p.name for p in ALL_PERSONAS],
    )
    def test_ir_has_tone(self, persona):
        """Each persona IR has a tone."""
        assert persona.ir.tone != ""

    @pytest.mark.parametrize(
        "persona",
        ALL_PERSONAS,
        ids=[p.name for p in ALL_PERSONAS],
    )
    def test_ir_has_confidence(self, persona):
        """Each persona IR has a confidence threshold."""
        assert persona.ir.confidence_threshold is not None
        assert 0 < persona.ir.confidence_threshold <= 1.0


class TestSpecificPersonas:
    """Spot-checks on key persona attributes."""

    def test_analyst_domain(self):
        assert "data analysis" in Analyst.ir.domain
        assert Analyst.ir.cite_sources is True

    def test_legal_refuse_if(self):
        assert "speculation" in LegalExpert.ir.refuse_if
        assert LegalExpert.ir.confidence_threshold == 0.90

    def test_coder_no_refuse(self):
        assert Coder.ir.refuse_if == ()
        assert Coder.ir.tone == "technical"

    def test_researcher_cites(self):
        assert Researcher.ir.cite_sources is True

    def test_writer_creative(self):
        assert Writer.ir.tone == "creative"
        assert Writer.ir.confidence_threshold == 0.75

    def test_summarizer_friendly(self):
        assert Summarizer.ir.tone == "friendly"

    def test_critic_formal(self):
        assert Critic.ir.tone == "formal"
        assert Critic.ir.cite_sources is True

    def test_translator_conversational(self):
        assert Translator.ir.tone == "conversational"
