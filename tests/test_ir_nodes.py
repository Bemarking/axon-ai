"""
AXON IR Nodes — Unit Tests
============================
Verifies structure, immutability, and serialization of all IR nodes.
"""

import pytest

from axon.compiler.ir_nodes import (
    IRNode,
    IRProgram,
    IRImport,
    IRPersona,
    IRContext,
    IRAnchor,
    IRToolSpec,
    IRMemory,
    IRType,
    IRTypeField,
    IRFlow,
    IRParameter,
    IRStep,
    IRIntent,
    IRProbe,
    IRReason,
    IRWeave,
    IRValidate,
    IRValidateRule,
    IRRefine,
    IRUseTool,
    IRRemember,
    IRRecall,
    IRConditional,
    IRRun,
)


# ═══════════════════════════════════════════════════════════════════
#  BASE NODE
# ═══════════════════════════════════════════════════════════════════


class TestIRNodeBase:
    """Base IRNode structure and serialization."""

    def test_default_construction(self):
        node = IRNode()
        assert node.node_type == ""
        assert node.source_line == 0
        assert node.source_column == 0

    def test_to_dict_includes_node_type(self):
        node = IRNode(node_type="test", source_line=5, source_column=10)
        d = node.to_dict()
        assert d["node_type"] == "test"
        assert d["source_line"] == 5
        assert d["source_column"] == 10

    def test_immutability(self):
        node = IRNode(node_type="test")
        with pytest.raises(AttributeError):
            node.node_type = "changed"  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════
#  DECLARATION NODES
# ═══════════════════════════════════════════════════════════════════


class TestIRPersona:
    """Persona IR node construction and serialization."""

    def test_full_persona(self):
        persona = IRPersona(
            name="LegalExpert",
            domain=("contract law", "IP"),
            tone="precise",
            confidence_threshold=0.85,
            cite_sources=True,
            refuse_if=("medical advice",),
            language="en",
            description="An expert in legal matters",
            source_line=1,
        )
        assert persona.name == "LegalExpert"
        assert persona.domain == ("contract law", "IP")
        assert persona.confidence_threshold == 0.85
        assert persona.cite_sources is True

    def test_persona_to_dict(self):
        persona = IRPersona(name="Test", domain=("AI",))
        d = persona.to_dict()
        assert d["node_type"] == "persona"
        assert d["name"] == "Test"
        assert d["domain"] == ("AI",)

    def test_minimal_persona(self):
        persona = IRPersona(name="MinimalBot")
        assert persona.name == "MinimalBot"
        assert persona.domain == ()
        assert persona.confidence_threshold is None


class TestIRContext:
    """Context IR node construction and serialization."""

    def test_full_context(self):
        ctx = IRContext(
            name="LegalSession",
            memory_scope="session",
            language="en",
            depth="deep",
            max_tokens=4000,
            temperature=0.3,
            cite_sources=True,
        )
        assert ctx.depth == "deep"
        assert ctx.max_tokens == 4000
        assert ctx.temperature == 0.3

    def test_context_to_dict(self):
        ctx = IRContext(name="Test", depth="shallow")
        d = ctx.to_dict()
        assert d["node_type"] == "context"
        assert d["depth"] == "shallow"


class TestIRAnchor:
    """Anchor IR node construction and serialization."""

    def test_full_anchor(self):
        anchor = IRAnchor(
            name="NoHallucination",
            require="factual accuracy",
            reject=("speculation", "guessing"),
            enforce="cite sources",
            confidence_floor=0.9,
            unknown_response="I'm not sure about that.",
            on_violation="raise",
            on_violation_target="HallucinationError",
        )
        assert anchor.name == "NoHallucination"
        assert anchor.reject == ("speculation", "guessing")
        assert anchor.confidence_floor == 0.9

    def test_anchor_to_dict(self):
        anchor = IRAnchor(name="NoBias", enforce="no stereotypes")
        d = anchor.to_dict()
        assert d["node_type"] == "anchor"
        assert d["enforce"] == "no stereotypes"


class TestIRToolSpec:
    """Tool spec IR node."""

    def test_tool_spec(self):
        tool = IRToolSpec(
            name="GoogleSearch",
            provider="google",
            max_results=5,
            timeout="10s",
        )
        assert tool.name == "GoogleSearch"
        assert tool.max_results == 5


class TestIRImport:
    """Import IR node."""

    def test_import(self):
        imp = IRImport(
            module_path=("axon", "anchors"),
            names=("NoHallucination", "NoBias"),
        )
        assert imp.module_path == ("axon", "anchors")
        assert len(imp.names) == 2


class TestIRMemory:
    """Memory IR node."""

    def test_memory(self):
        mem = IRMemory(
            name="ConversationLog",
            store="persistent",
            backend="vector_db",
            retrieval="semantic",
            decay="weekly",
        )
        assert mem.store == "persistent"
        assert mem.retrieval == "semantic"


# ═══════════════════════════════════════════════════════════════════
#  TYPE SYSTEM NODES
# ═══════════════════════════════════════════════════════════════════


class TestIRType:
    """Type definition IR nodes."""

    def test_structured_type(self):
        t = IRType(
            name="Party",
            fields=(
                IRTypeField(name="name", type_name="FactualClaim"),
                IRTypeField(name="role", type_name="String"),
            ),
        )
        assert t.name == "Party"
        assert len(t.fields) == 2
        assert t.fields[0].type_name == "FactualClaim"

    def test_ranged_type(self):
        t = IRType(name="RiskScore", range_min=0.0, range_max=1.0)
        assert t.range_min == 0.0
        assert t.range_max == 1.0

    def test_constrained_type(self):
        t = IRType(
            name="HighConfidence",
            where_expression="confidence >= 0.85",
        )
        assert t.where_expression == "confidence >= 0.85"

    def test_type_to_dict_with_nested_fields(self):
        t = IRType(
            name="Party",
            fields=(IRTypeField(name="name", type_name="String"),),
        )
        d = t.to_dict()
        assert d["node_type"] == "type_def"
        assert isinstance(d["fields"], tuple)
        # Each field element should be a dict (serialized IRTypeField)
        field_d = d["fields"][0]
        assert isinstance(field_d, dict)
        assert field_d["name"] == "name"


# ═══════════════════════════════════════════════════════════════════
#  FLOW & STEP NODES
# ═══════════════════════════════════════════════════════════════════


class TestIRFlow:
    """Flow IR node construction."""

    def test_flow_with_steps(self):
        flow = IRFlow(
            name="AnalyzeContract",
            parameters=(
                IRParameter(name="doc", type_name="Document"),
            ),
            return_type_name="ContractAnalysis",
            steps=(
                IRStep(name="extract_parties", ask="Find all parties"),
                IRStep(name="analyze_clauses", ask="Analyze key clauses"),
            ),
        )
        assert flow.name == "AnalyzeContract"
        assert len(flow.parameters) == 1
        assert len(flow.steps) == 2

    def test_empty_flow(self):
        flow = IRFlow(name="EmptyFlow")
        assert flow.steps == ()
        assert flow.parameters == ()


class TestIRStep:
    """Step IR node with embedded operations."""

    def test_step_with_probe(self):
        step = IRStep(
            name="extract",
            given="document",
            probe=IRProbe(target="doc", fields=("name", "date")),
            output_type="PartyList",
        )
        assert step.probe is not None
        assert step.probe.fields == ("name", "date")

    def test_step_with_tool(self):
        step = IRStep(
            name="search",
            use_tool=IRUseTool(tool_name="GoogleSearch", argument="query"),
        )
        assert step.use_tool is not None
        assert step.use_tool.tool_name == "GoogleSearch"

    def test_step_with_ask(self):
        step = IRStep(name="think", ask="What are the implications?")
        assert step.ask == "What are the implications?"


# ═══════════════════════════════════════════════════════════════════
#  COGNITIVE NODES
# ═══════════════════════════════════════════════════════════════════


class TestCognitiveNodes:
    """Intent, Probe, Reason, Weave, Validate, Refine."""

    def test_intent(self):
        intent = IRIntent(
            name="classify_risk",
            given="contract",
            ask="Classify the risk level",
            output_type_name="RiskScore",
            confidence_floor=0.85,
        )
        assert intent.output_type_name == "RiskScore"
        assert intent.confidence_floor == 0.85

    def test_probe(self):
        probe = IRProbe(target="document", fields=("name", "date", "amount"))
        assert len(probe.fields) == 3

    def test_reason_chain(self):
        reason = IRReason(
            about="risk",
            given=("parties", "clauses"),
            depth=3,
            show_work=True,
            chain_of_thought=True,
            ask="What is the overall risk?",
            output_type="RiskAssessment",
        )
        assert reason.depth == 3
        assert reason.show_work is True
        assert len(reason.given) == 2

    def test_weave(self):
        weave = IRWeave(
            sources=("risk_analysis", "party_data"),
            target="FinalReport",
            format_type="markdown",
            priority=("risk", "compliance"),
            style="formal",
        )
        assert len(weave.sources) == 2
        assert weave.format_type == "markdown"

    def test_validate(self):
        validate = IRValidate(
            target="output",
            schema="ContractAnalysis",
            rules=(
                IRValidateRule(
                    condition="confidence",
                    comparison_op=">=",
                    comparison_value="0.85",
                    action="refine",
                ),
            ),
        )
        assert len(validate.rules) == 1
        assert validate.rules[0].action == "refine"

    def test_refine(self):
        refine = IRRefine(
            max_attempts=5,
            pass_failure_context=True,
            backoff="exponential",
            on_exhaustion="raise",
            on_exhaustion_target="QualityError",
        )
        assert refine.max_attempts == 5
        assert refine.backoff == "exponential"


class TestMemoryOps:
    """Remember and Recall IR nodes."""

    def test_remember(self):
        r = IRRemember(expression="analysis_result", memory_target="ConversationLog")
        assert r.expression == "analysis_result"

    def test_recall(self):
        r = IRRecall(query="previous analysis", memory_source="ConversationLog")
        assert r.query == "previous analysis"


class TestConditional:
    """Conditional IR node."""

    def test_conditional_with_branches(self):
        cond = IRConditional(
            condition="confidence",
            comparison_op=">=",
            comparison_value="0.85",
            then_branch=IRStep(name="accept", ask="Accept the result"),
            else_branch=IRStep(name="retry", ask="Retry with more data"),
        )
        assert cond.then_branch is not None
        assert cond.else_branch is not None

    def test_conditional_to_dict_serializes_branches(self):
        cond = IRConditional(
            condition="score",
            comparison_op=">",
            comparison_value="0.5",
            then_branch=IRStep(name="pass"),
        )
        d = cond.to_dict()
        assert d["then_branch"]["name"] == "pass"
        assert d["else_branch"] is None


# ═══════════════════════════════════════════════════════════════════
#  EXECUTION & PROGRAM
# ═══════════════════════════════════════════════════════════════════


class TestIRRun:
    """Run statement IR node."""

    def test_run_with_resolved_refs(self):
        persona = IRPersona(name="LegalExpert")
        context = IRContext(name="LegalSession")
        anchor = IRAnchor(name="NoHallucination")
        flow = IRFlow(name="AnalyzeContract")

        run = IRRun(
            flow_name="AnalyzeContract",
            persona_name="LegalExpert",
            context_name="LegalSession",
            anchor_names=("NoHallucination",),
            resolved_flow=flow,
            resolved_persona=persona,
            resolved_context=context,
            resolved_anchors=(anchor,),
            effort="high",
        )
        assert run.resolved_flow is not None
        assert run.resolved_persona is not None
        assert run.resolved_context is not None
        assert len(run.resolved_anchors) == 1


class TestIRProgram:
    """Program root IR node."""

    def test_empty_program(self):
        prog = IRProgram()
        assert prog.node_type == "program"
        assert prog.personas == ()
        assert prog.flows == ()
        assert prog.runs == ()

    def test_full_program_structure(self):
        persona = IRPersona(name="Expert")
        context = IRContext(name="Session")
        anchor = IRAnchor(name="NoHallucination")
        flow = IRFlow(name="Analyze", steps=(IRStep(name="s1"),))
        run = IRRun(
            flow_name="Analyze",
            persona_name="Expert",
            context_name="Session",
            resolved_flow=flow,
            resolved_persona=persona,
            resolved_context=context,
        )

        prog = IRProgram(
            personas=(persona,),
            contexts=(context,),
            anchors=(anchor,),
            flows=(flow,),
            runs=(run,),
        )

        assert len(prog.personas) == 1
        assert len(prog.flows) == 1
        assert len(prog.runs) == 1

    def test_program_serialization(self):
        prog = IRProgram(
            personas=(IRPersona(name="Bot"),),
            flows=(IRFlow(name="Run"),),
        )
        d = prog.to_dict()
        assert d["node_type"] == "program"
        assert isinstance(d["personas"], tuple)
        # Nested node should be serialized as dict
        assert isinstance(d["personas"][0], dict)
        assert d["personas"][0]["name"] == "Bot"
