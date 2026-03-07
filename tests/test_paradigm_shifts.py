"""
Test Suite — AXON Paradigm Shift Constructs
=============================================
Comprehensive tests for:
  1. Epistemic Directives (know, believe, speculate, doubt)
  2. Parallel Cognitive Dispatch (par)
  3. Dynamic State Yielding (hibernate)

Tests cover the full pipeline: Lex → Parse → TypeCheck → IR → Serialization
"""

from __future__ import annotations

import asyncio

import pytest

from axon.compiler.ast_nodes import (
    EpistemicBlock,
    FlowDefinition,
    HibernateNode,
    ParallelBlock,
    StepNode,
)
from axon.compiler.ir_generator import IRGenerator
from axon.compiler.ir_nodes import (
    IREpistemicBlock,
    IRFlow,
    IRHibernate,
    IRParallelBlock,
    IRStep,
)
from axon.compiler.lexer import Lexer
from axon.compiler.parser import Parser
from axon.compiler.tokens import TokenType
from axon.compiler.type_checker import TypeChecker
from axon.runtime.state_backend import (
    ExecutionState,
    InMemoryStateBackend,
    StateBackend,
)


# ═══════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════

def lex(source: str) -> list:
    return Lexer(source).tokenize()


def parse(source: str):
    tokens = lex(source)
    return Parser(tokens).parse()


def check(source: str) -> list:
    program = parse(source)
    tc = TypeChecker(program)
    return tc.check()


def generate_ir(source: str):
    program = parse(source)
    TypeChecker(program).check()
    gen = IRGenerator()
    return gen.generate(program)


# ═══════════════════════════════════════════════════════════════════
#  PART 1 — EPISTEMIC DIRECTIVES
# ═══════════════════════════════════════════════════════════════════


class TestEpistemicTokens:
    """Verify the lexer recognizes all 4 epistemic keywords."""

    @pytest.mark.parametrize("keyword,expected", [
        ("know", TokenType.KNOW),
        ("believe", TokenType.BELIEVE),
        ("speculate", TokenType.SPECULATE),
        ("doubt", TokenType.DOUBT),
    ])
    def test_epistemic_keyword_recognized(self, keyword, expected):
        tokens = lex(keyword)
        assert tokens[0].type == expected
        assert tokens[0].value == keyword

    def test_epistemic_not_identifier(self):
        """Epistemic keywords should NOT be parsed as identifiers."""
        for kw in ("know", "believe", "speculate", "doubt"):
            tokens = lex(kw)
            assert tokens[0].type != TokenType.IDENTIFIER


class TestEpistemicParser:
    """Verify parser produces correct EpistemicBlock AST nodes."""

    def test_know_block_parses(self):
        src = '''
        know {
            flow Summarize(doc: Document) -> Fact {
                step Extract { ask: "Extract facts" output: Fact }
            }
        }
        '''
        program = parse(src)
        assert len(program.declarations) == 1
        block = program.declarations[0]
        assert isinstance(block, EpistemicBlock)
        assert block.mode == "know"
        assert len(block.body) == 1
        assert isinstance(block.body[0], FlowDefinition)
        assert block.body[0].name == "Summarize"

    @pytest.mark.parametrize("mode", ["know", "believe", "speculate", "doubt"])
    def test_all_modes_parse(self, mode):
        src = f'''
        {mode} {{
            flow Test(x: String) -> String {{
                step Do {{ ask: "test" output: String }}
            }}
        }}
        '''
        program = parse(src)
        block = program.declarations[0]
        assert isinstance(block, EpistemicBlock)
        assert block.mode == mode

    def test_nested_epistemic_multiple_declarations(self):
        src = '''
        know {
            flow A(x: String) -> String {
                step S1 { ask: "a" output: String }
            }
            flow B(y: String) -> String {
                step S2 { ask: "b" output: String }
            }
        }
        '''
        program = parse(src)
        block = program.declarations[0]
        assert isinstance(block, EpistemicBlock)
        assert len(block.body) == 2

    def test_epistemic_block_line_tracking(self):
        src = 'know { flow A(d: Document) -> Fact { step S { ask: "x" output: Fact } } }'
        program = parse(src)
        block = program.declarations[0]
        assert block.line == 1


class TestEpistemicTypeChecker:
    """Verify type checker validates epistemic blocks."""

    def test_valid_know_block(self):
        src = '''
        type Fact
        know {
            flow Summarize(doc: String) -> Fact {
                step Extract { ask: "Get facts" output: Fact }
            }
        }
        '''
        errors = check(src)
        assert errors == []

    def test_empty_know_block_valid(self):
        src = 'know { }'
        errors = check(src)
        assert errors == []


class TestEpistemicIR:
    """Verify IR generator produces correct IREpistemicBlock nodes."""

    def test_know_block_ir_constraints(self):
        src = '''
        type Fact
        know {
            flow Summarize(doc: String) -> Fact {
                step Extract { ask: "Get facts" output: Fact }
            }
        }
        '''
        ir = generate_ir(src)
        # The know block should be in the IR
        # Find the IREpistemicBlock — it may be visited during flow collection
        # Actually, epistemic blocks produce IREpistemicBlock in the visitors
        # Let's check the flow was registered
        assert len(ir.flows) == 1
        assert ir.flows[0].name == "Summarize"

    def test_know_constraints_applied(self):
        src = '''
        know {
            flow A(x: String) -> String {
                step S { ask: "x" output: String }
            }
        }
        '''
        program = parse(src)
        gen = IRGenerator()
        # Visit the epistemic block directly
        block = program.declarations[0]
        ir_block = gen._visit(block)
        assert isinstance(ir_block, IREpistemicBlock)
        assert ir_block.mode == "know"
        assert ir_block.temperature_override == 0.1
        assert ir_block.top_p_override == 0.3
        assert "RequiresCitation" in ir_block.injected_anchors
        assert "NoHallucination" in ir_block.injected_anchors

    def test_speculate_constraints_relaxed(self):
        src = '''
        speculate {
            flow Brainstorm(topic: String) -> String {
                step Think { ask: "brainstorm" output: String }
            }
        }
        '''
        program = parse(src)
        gen = IRGenerator()
        block = program.declarations[0]
        ir_block = gen._visit(block)
        assert ir_block.mode == "speculate"
        assert ir_block.temperature_override == 0.9
        assert ir_block.top_p_override == 0.95
        assert ir_block.injected_anchors == ()

    def test_believe_constraints_moderate(self):
        src = '''
        believe {
            flow Assess(data: String) -> String {
                step Eval { ask: "assess" output: String }
            }
        }
        '''
        program = parse(src)
        gen = IRGenerator()
        ir_block = gen._visit(program.declarations[0])
        assert ir_block.mode == "believe"
        assert ir_block.temperature_override == 0.3
        assert ir_block.top_p_override == 0.5
        assert "NoHallucination" in ir_block.injected_anchors
        assert len(ir_block.injected_anchors) == 1

    def test_doubt_constraints_analytical(self):
        src = '''
        doubt {
            flow Verify(claim: String) -> String {
                step Check { ask: "verify" output: String }
            }
        }
        '''
        program = parse(src)
        gen = IRGenerator()
        ir_block = gen._visit(program.declarations[0])
        assert ir_block.mode == "doubt"
        assert ir_block.temperature_override == 0.2
        assert ir_block.top_p_override == 0.4
        assert "RequiresCitation" in ir_block.injected_anchors
        assert "SyllogismChecker" in ir_block.injected_anchors

    def test_epistemic_ir_serialization(self):
        src = '''
        know {
            flow A(x: String) -> String {
                step S { ask: "x" output: String }
            }
        }
        '''
        program = parse(src)
        gen = IRGenerator()
        ir_block = gen._visit(program.declarations[0])
        d = ir_block.to_dict()
        assert d["node_type"] == "epistemic_block"
        assert d["mode"] == "know"
        assert d["temperature_override"] == 0.1


# ═══════════════════════════════════════════════════════════════════
#  PART 2 — PARALLEL COGNITIVE DISPATCH
# ═══════════════════════════════════════════════════════════════════


class TestParallelTokens:
    """Verify the lexer recognizes par and consolidate."""

    def test_par_keyword(self):
        tokens = lex("par")
        assert tokens[0].type == TokenType.PAR

    def test_consolidate_keyword(self):
        tokens = lex("consolidate")
        assert tokens[0].type == TokenType.CONSOLIDATE


class TestParallelParser:
    """Verify parser produces correct ParallelBlock AST nodes."""

    def test_par_block_parses(self):
        src = '''
        flow Analyze(doc: Document) -> Report {
            par {
                step Financial { ask: "Analyze financials" output: FinancialReport }
                step Legal { ask: "Analyze liabilities" output: LegalReport }
            }
        }
        '''
        program = parse(src)
        flow = program.declarations[0]
        assert isinstance(flow, FlowDefinition)
        par = flow.body[0]
        assert isinstance(par, ParallelBlock)
        assert len(par.branches) == 2
        assert isinstance(par.branches[0], StepNode)
        assert par.branches[0].name == "Financial"
        assert par.branches[1].name == "Legal"

    def test_par_three_branches(self):
        src = '''
        flow Multi(x: String) -> String {
            par {
                step A { ask: "a" output: String }
                step B { ask: "b" output: String }
                step C { ask: "c" output: String }
            }
        }
        '''
        program = parse(src)
        par = program.declarations[0].body[0]
        assert isinstance(par, ParallelBlock)
        assert len(par.branches) == 3

    def test_par_mixed_with_sequential_steps(self):
        src = '''
        flow Pipeline(x: String) -> String {
            step First { ask: "first" output: String }
            par {
                step A { ask: "parallel a" output: String }
                step B { ask: "parallel b" output: String }
            }
            step Last { ask: "last" output: String }
        }
        '''
        program = parse(src)
        flow = program.declarations[0]
        assert len(flow.body) == 3
        assert isinstance(flow.body[0], StepNode)
        assert isinstance(flow.body[1], ParallelBlock)
        assert isinstance(flow.body[2], StepNode)

    def test_par_block_line_tracking(self):
        src = '''
        flow Test(x: String) -> String {
            par {
                step A { ask: "a" output: String }
                step B { ask: "b" output: String }
            }
        }
        '''
        program = parse(src)
        par = program.declarations[0].body[0]
        assert par.line > 0


class TestParallelTypeChecker:
    """Verify type checker validates parallel blocks."""

    def test_valid_par_block(self):
        src = '''
        flow Analyze(x: String) -> String {
            par {
                step A { ask: "a" output: String }
                step B { ask: "b" output: String }
            }
        }
        '''
        errors = check(src)
        assert errors == []

    def test_single_branch_par_error(self):
        src = '''
        flow Bad(x: String) -> String {
            par {
                step Only { ask: "solo" output: String }
            }
        }
        '''
        # Parser allows single-branch par, but type checker should flag it
        # The par block in _parse_flow_step collects all steps until }
        program = parse(src)
        flow = program.declarations[0]
        par = flow.body[0]
        assert isinstance(par, ParallelBlock)
        assert len(par.branches) == 1  # Parser accepted it
        # Type checker should emit error
        errors = check(src)
        assert len(errors) >= 1
        assert "at least 2" in str(errors[0])


class TestParallelIR:
    """Verify IR generation for parallel blocks."""

    def test_par_ir_branches(self):
        src = '''
        flow Analyze(x: String) -> String {
            par {
                step A { ask: "a" output: String }
                step B { ask: "b" output: String }
            }
        }
        '''
        program = parse(src)
        gen = IRGenerator()
        # Visit flow to get the par block in the step tree
        flow_node = program.declarations[0]
        ir_flow = gen._visit(flow_node)
        # The par block should be one of the steps
        par_step = ir_flow.steps[0]
        assert isinstance(par_step, IRParallelBlock)
        assert len(par_step.branches) == 2
        assert isinstance(par_step.branches[0], IRStep)
        assert isinstance(par_step.branches[1], IRStep)

    def test_par_ir_serialization(self):
        src = '''
        flow Test(x: String) -> String {
            par {
                step A { ask: "a" output: String }
                step B { ask: "b" output: String }
            }
        }
        '''
        program = parse(src)
        gen = IRGenerator()
        ir_flow = gen._visit(program.declarations[0])
        par = ir_flow.steps[0]
        d = par.to_dict()
        assert d["node_type"] == "parallel_block"
        assert len(d["branches"]) == 2


# ═══════════════════════════════════════════════════════════════════
#  PART 3 — DYNAMIC STATE YIELDING
# ═══════════════════════════════════════════════════════════════════


class TestHibernateTokens:
    """Verify the lexer recognizes hibernate."""

    def test_hibernate_keyword(self):
        tokens = lex("hibernate")
        assert tokens[0].type == TokenType.HIBERNATE

    def test_hibernate_not_identifier(self):
        tokens = lex("hibernate")
        assert tokens[0].type != TokenType.IDENTIFIER


class TestHibernateParser:
    """Verify parser produces correct HibernateNode AST nodes."""

    def test_hibernate_with_event(self):
        src = '''
        flow Monitor(id: String) -> String {
            step Analyze { ask: "analyze" output: String }
            hibernate until "amendment_received"
            step Reanalyze { ask: "reanalyze" output: String }
        }
        '''
        program = parse(src)
        flow = program.declarations[0]
        assert len(flow.body) == 3
        assert isinstance(flow.body[0], StepNode)
        assert isinstance(flow.body[1], HibernateNode)
        assert isinstance(flow.body[2], StepNode)

        hib = flow.body[1]
        assert hib.event_name == "amendment_received"

    def test_hibernate_multiple_checkpoints(self):
        src = '''
        flow LongRunning(x: String) -> String {
            step Phase1 { ask: "phase 1" output: String }
            hibernate until "approval_received"
            step Phase2 { ask: "phase 2" output: String }
            hibernate until "data_updated"
            step Phase3 { ask: "phase 3" output: String }
        }
        '''
        program = parse(src)
        flow = program.declarations[0]
        assert len(flow.body) == 5
        assert isinstance(flow.body[1], HibernateNode)
        assert isinstance(flow.body[3], HibernateNode)
        assert flow.body[1].event_name == "approval_received"
        assert flow.body[3].event_name == "data_updated"

    def test_hibernate_line_tracking(self):
        src = 'flow T(x: String) -> String { hibernate until "event" }'
        program = parse(src)
        hib = program.declarations[0].body[0]
        assert isinstance(hib, HibernateNode)
        assert hib.line == 1


class TestHibernateTypeChecker:
    """Verify type checker validates hibernate nodes."""

    def test_valid_hibernate(self):
        src = '''
        flow Monitor(id: String) -> String {
            step Analyze { ask: "analyze" output: String }
            hibernate until "amendment_received"
        }
        '''
        errors = check(src)
        assert errors == []

    def test_hibernate_without_event_error(self):
        """hibernate without 'until' should produce a type error."""
        src = '''
        flow Bad(x: String) -> String {
            hibernate
        }
        '''
        # Parser accepts bare hibernate, type checker flags missing event
        errors = check(src)
        assert len(errors) >= 1
        assert "event name" in str(errors[0]).lower()


class TestHibernateIR:
    """Verify IR generation for hibernate nodes."""

    def test_hibernate_ir_node(self):
        src = '''
        flow Monitor(id: String) -> String {
            step Analyze { ask: "analyze" output: String }
            hibernate until "amendment_received"
        }
        '''
        program = parse(src)
        gen = IRGenerator()
        ir_flow = gen._visit(program.declarations[0])
        hib = ir_flow.steps[1]
        assert isinstance(hib, IRHibernate)
        assert hib.event_name == "amendment_received"
        assert hib.node_type == "hibernate"

    def test_hibernate_continuation_id_deterministic(self):
        """Same source position → same continuation ID."""
        src = 'flow T(x: String) -> String { hibernate until "event" }'
        program1 = parse(src)
        program2 = parse(src)
        gen1 = IRGenerator()
        gen2 = IRGenerator()
        ir1 = gen1._visit(program1.declarations[0])
        ir2 = gen2._visit(program2.declarations[0])
        assert ir1.steps[0].continuation_id == ir2.steps[0].continuation_id

    def test_hibernate_continuation_id_unique_per_event(self):
        """Different events → different continuation IDs."""
        src1 = 'flow T(x: String) -> String { hibernate until "event_a" }'
        src2 = 'flow T(x: String) -> String { hibernate until "event_b" }'
        gen = IRGenerator()
        ir1 = gen._visit(parse(src1).declarations[0])
        gen2 = IRGenerator()
        ir2 = gen2._visit(parse(src2).declarations[0])
        assert ir1.steps[0].continuation_id != ir2.steps[0].continuation_id

    def test_hibernate_ir_serialization(self):
        src = 'flow T(x: String) -> String { hibernate until "event" }'
        program = parse(src)
        gen = IRGenerator()
        ir_flow = gen._visit(program.declarations[0])
        d = ir_flow.steps[0].to_dict()
        assert d["node_type"] == "hibernate"
        assert d["event_name"] == "event"
        assert len(d["continuation_id"]) == 16


# ═══════════════════════════════════════════════════════════════════
#  PART 4 — STATE BACKEND
# ═══════════════════════════════════════════════════════════════════


class TestExecutionState:
    """Verify ExecutionState serialization/deserialization."""

    def test_serialize_deserialize_roundtrip(self):
        state = ExecutionState(
            continuation_id="abc123",
            flow_name="AnalyzeContract",
            event_name="amendment_received",
            step_index=3,
            step_results={"Phase1": "done"},
            context_vars={"doc": "contract.pdf"},
            system_prompt="You are a legal analyst",
            persona_name="Lawyer",
            context_name="LegalReview",
            effort="high",
        )
        data = state.serialize()
        restored = ExecutionState.deserialize(data)
        assert restored.continuation_id == "abc123"
        assert restored.flow_name == "AnalyzeContract"
        assert restored.event_name == "amendment_received"
        assert restored.step_index == 3
        assert restored.step_results == {"Phase1": "done"}
        assert restored.context_vars == {"doc": "contract.pdf"}
        assert restored.persona_name == "Lawyer"

    def test_empty_state_serialization(self):
        state = ExecutionState()
        data = state.serialize()
        restored = ExecutionState.deserialize(data)
        assert restored.continuation_id == ""
        assert restored.step_results == {}


class TestInMemoryStateBackend:
    """Verify InMemoryStateBackend implements StateBackend correctly."""

    def test_protocol_compliance(self):
        backend = InMemoryStateBackend()
        assert isinstance(backend, StateBackend)

    def test_save_and_load(self):
        backend = InMemoryStateBackend()
        state = ExecutionState(
            continuation_id="test123",
            flow_name="Monitor",
            event_name="update",
        )
        data = state.serialize()
        asyncio.run(backend.save_state("test123", data))
        loaded = asyncio.run(backend.load_state("test123"))
        assert loaded is not None
        restored = ExecutionState.deserialize(loaded)
        assert restored.flow_name == "Monitor"

    def test_load_nonexistent_returns_none(self):
        backend = InMemoryStateBackend()
        result = asyncio.run(backend.load_state("nonexistent"))
        assert result is None

    def test_delete_state(self):
        backend = InMemoryStateBackend()
        asyncio.run(backend.save_state("id1", b"data"))
        asyncio.run(backend.delete_state("id1"))
        result = asyncio.run(backend.load_state("id1"))
        assert result is None

    def test_list_pending(self):
        backend = InMemoryStateBackend()
        asyncio.run(backend.save_state("a", b"1"))
        asyncio.run(backend.save_state("b", b"2"))
        pending = asyncio.run(backend.list_pending())
        assert set(pending) == {"a", "b"}

    def test_delete_nonexistent_no_error(self):
        backend = InMemoryStateBackend()
        asyncio.run(backend.delete_state("nope"))  # should not raise


# ═══════════════════════════════════════════════════════════════════
#  PART 5 — INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════


class TestIntegrationEpistemic:
    """Full pipeline integration for epistemic blocks."""

    def test_know_flow_full_pipeline(self):
        src = '''
        type Evidence
        persona Scientist {
            domain: ["research"]
            tone: precise
        }
        context Research {
            memory: session
            depth: exhaustive
        }
        know {
            flow AnalyzeEvidence(data: String) -> Evidence {
                step Extract { ask: "Extract evidence" output: Evidence }
            }
        }
        run AnalyzeEvidence("sample_data.csv")
            as Scientist
            within Research
        '''
        ir = generate_ir(src)
        assert len(ir.flows) == 1
        assert ir.flows[0].name == "AnalyzeEvidence"
        assert len(ir.runs) == 1

    def test_speculate_flow_full_pipeline(self):
        src = '''
        speculate {
            flow Imagine(topic: String) -> String {
                step Dream { ask: "Imagine possibilities" output: String }
            }
        }
        '''
        ir = generate_ir(src)
        assert len(ir.flows) == 1


class TestIntegrationParallel:
    """Full pipeline integration for parallel dispatch."""

    def test_par_in_flow_full_pipeline(self):
        src = '''
        type Report
        flow FullAnalysis(doc: String) -> Report {
            par {
                step Financial { ask: "Analyze money" output: Report }
                step Legal { ask: "Analyze law" output: Report }
                step Compliance { ask: "Check rules" output: Report }
            }
            weave [Financial, Legal, Compliance] into Final {
                format: Report
            }
        }
        '''
        ir = generate_ir(src)
        assert len(ir.flows) == 1
        flow = ir.flows[0]
        # First step should be the par block
        assert isinstance(flow.steps[0], IRParallelBlock)
        assert len(flow.steps[0].branches) == 3


class TestIntegrationHibernate:
    """Full pipeline integration for hibernate/resume."""

    def test_hibernate_in_flow_full_pipeline(self):
        src = '''
        flow MonitorContract(id: String) -> String {
            step InitialAnalysis { ask: "Initial scan" output: String }
            hibernate until "contract_amended"
            step FollowUp { ask: "Re-evaluate" output: String }
        }
        '''
        ir = generate_ir(src)
        assert len(ir.flows) == 1
        flow = ir.flows[0]
        assert len(flow.steps) == 3
        assert isinstance(flow.steps[1], IRHibernate)
        assert flow.steps[1].event_name == "contract_amended"

    def test_state_backend_with_real_execution_state(self):
        """Round-trip: IR → State → Persist → Load → Resume-ready."""
        src = 'flow M(x: String) -> String { hibernate until "wake_up" }'
        ir = generate_ir(src)
        flow = ir.flows[0]
        hib = flow.steps[0]

        # Build execution state at this point
        state = ExecutionState(
            continuation_id=hib.continuation_id,
            flow_name=flow.name,
            event_name=hib.event_name,
            step_index=0,
            system_prompt="You are an analyst",
        )
        data = state.serialize()
        backend = InMemoryStateBackend()
        asyncio.run(backend.save_state(hib.continuation_id, data))

        # Later: load and verify
        loaded = asyncio.run(backend.load_state(hib.continuation_id))
        restored = ExecutionState.deserialize(loaded)
        assert restored.continuation_id == hib.continuation_id
        assert restored.flow_name == "M"
        assert restored.event_name == "wake_up"


class TestIntegrationCombined:
    """Tests combining multiple paradigm shifts in a single program."""

    def test_all_three_paradigms_in_one_program(self):
        src = '''
        type Evidence
        type Report

        know {
            flow ExtractFacts(doc: String) -> Evidence {
                step Extract { ask: "Extract verified facts" output: Evidence }
            }
        }

        flow FullPipeline(doc: String) -> Report {
            par {
                step Analysis { ask: "Deep analysis" output: Report }
                step Review { ask: "Peer review" output: Report }
            }
            hibernate until "human_approval"
            step Finalize { ask: "Create final report" output: Report }
        }

        speculate {
            flow BrainstormNext(report: String) -> String {
                step Ideas { ask: "What could improve?" output: String }
            }
        }
        '''
        ir = generate_ir(src)
        assert len(ir.flows) == 3
        flow_names = {f.name for f in ir.flows}
        assert flow_names == {"ExtractFacts", "FullPipeline", "BrainstormNext"}

        # Verify FullPipeline structure
        pipeline = next(f for f in ir.flows if f.name == "FullPipeline")
        assert isinstance(pipeline.steps[0], IRParallelBlock)
        assert isinstance(pipeline.steps[1], IRHibernate)
        assert isinstance(pipeline.steps[2], IRStep)

    def test_par_inside_know_block(self):
        """Parallel dispatch inside an epistemic scope."""
        src = '''
        know {
            flow DualVerify(data: String) -> String {
                par {
                    step FactCheck { ask: "Verify facts" output: String }
                    step SourceCheck { ask: "Verify sources" output: String }
                }
            }
        }
        '''
        ir = generate_ir(src)
        assert len(ir.flows) == 1
        flow = ir.flows[0]
        assert isinstance(flow.steps[0], IRParallelBlock)
