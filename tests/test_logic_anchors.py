import pytest

from axon.stdlib.anchors.checkers import (
    check_agnostic_fallback,
    check_chain_of_thought,
    check_requires_citation,
    check_syllogism,
)
from axon.stdlib.anchors.definitions import (
    AgnosticFallback,
    ChainOfThoughtValidator,
    RequiresCitation,
    SyllogismChecker,
)


def test_syllogism_checker():
    """Test syntax validation for logical arguments."""
    # Valid - Contains both markers
    valid_output = "Premise: All men are mortal. Conclusion: Socrates is mortal."
    passed, violations = check_syllogism(valid_output)
    assert passed is True
    assert len(violations) == 0

    # Invalid - Missing premise
    missing_premise = "Conclusion: Therefore it rains."
    passed, violations = check_syllogism(missing_premise)
    assert passed is False
    assert len(violations) == 1
    assert "Premise:' and 'Conclusion:' identifiers" in violations[0]

    # Invalid - Missing conclusion
    missing_conclusion = "Premise: The sky is blue."
    passed, violations = check_syllogism(missing_conclusion)
    assert passed is False
    assert len(violations) == 1

    # False Negative (Documented Behavior) - Valid logic without markers fails the structural check
    prose_logic = "Since all dogs bark, and Rex is a dog, Rex barks."
    passed, violations = check_syllogism(prose_logic)
    assert passed is False


def test_chain_of_thought_validator():
    """Test enforcement of reasoning step markers."""
    valid_cot = "Step 1: Calculate mass. Step 2: Apply gravity. Therefore, 9.8N."
    passed, violations = check_chain_of_thought(valid_cot)
    assert passed is True

    valid_cot_alt = "First, let's look at the data. Then we conclude."
    passed, violations = check_chain_of_thought(valid_cot_alt)
    assert passed is True

    invalid_direct = "The answer is 42."
    passed, violations = check_chain_of_thought(invalid_direct)
    assert passed is False
    assert "Use explicit markers" in violations[0]


def test_requires_citation():
    """Test enforcement of inline academic citations."""
    # Bracket style
    valid_bracket = "The earth is round [1]."
    passed, violations = check_requires_citation(valid_bracket)
    assert passed is True

    # Author, Year style
    valid_author = "The sky is blue (Smith, 2024)."
    passed, violations = check_requires_citation(valid_author)
    assert passed is True

    # URL style
    valid_url = "Based on data from https://example.com/data"
    passed, violations = check_requires_citation(valid_url)
    assert passed is True

    # Missing citation
    invalid_claim = "The capital of France is Paris."
    passed, violations = check_requires_citation(invalid_claim)
    assert passed is False
    assert "explicit inline citations" in violations[0]


def test_agnostic_fallback():
    """Test epistemic honesty and rejection of unwarranted guessing."""
    # Honest Ignorance - Should pass
    honest_ignorance = "I do not have sufficient data to answer this definitively."
    passed, violations = check_agnostic_fallback(honest_ignorance)
    assert passed is True

    # Speculation without ignorance - Should FAIL (Guesses to be helpful)
    helpful_guess = "I'm guessing it might be around 5 million."
    passed, violations = check_agnostic_fallback(helpful_guess)
    assert passed is False
    assert "unwarranted speculation" in violations[0]

    # Uncertain honesty - Should PASS (Admitting uncertainty while offering a hypothesis)
    epistemic_honesty = "I am unsure, but my best guess based on similar data..."
    passed, violations = check_agnostic_fallback(epistemic_honesty)
    assert passed is True


def test_anchor_interaction_conflicts():
    """Test theoretical conflicts between Epistemic Anchors."""
    # If a model falls back to Agnostic, it cannot provide citations.
    # A robust system shouldn't trigger RequiresCitation if AgnosticFallback triggers an honest ignorance.
    honest_ignorance = "I do not know the answer and lack sufficient data."
    
    # Agnostic anchor passes correctly
    passed_agnostic, _ = check_agnostic_fallback(honest_ignorance)
    assert passed_agnostic is True

    # RequiresCitation fails correctly (because it's a dumb regex checker)
    # The Executor handles this logic: If the model declares Uncertainty/Ignorance, 
    # HighConfidence anchors are bypassed structurally by the Type Checker before hitting here.
    passed_cite, viols = check_requires_citation(honest_ignorance)
    assert passed_cite is False
    assert len(viols) == 1


class _MockSelfHealingClient:
    """Mock client to test Self-Healing specifically with Logic Checkers."""
    
    def __init__(self, initial_response: str, corrected_response: str, expected_violation: str):
        self.initial_response = initial_response
        self.corrected_response = corrected_response
        self.expected_violation = expected_violation
        self.call_count = 0
        self.failure_contexts = []
        
    async def call(self, *args, **kwargs):
        self.call_count += 1
        
        from axon.runtime.executor import ModelResponse
        
        failure_context = kwargs.get("failure_context")
            
        if self.call_count == 1:
            assert not failure_context
            return ModelResponse(raw=self.initial_response, content=self.initial_response)
        
        # Second call (and beyond) should have the failure context injected
        assert failure_context is not None
        self.failure_contexts.append(failure_context)
        # Verify the failure context contains the specific logic/epistemic rejection
        print("ACTUAL FAILURE CONTEXT:\\n", failure_context)
        print("EXPECTED VIOLATION:\\n", self.expected_violation)
        assert self.expected_violation in failure_context
        
        return ModelResponse(raw=self.corrected_response, content=self.corrected_response)

def test_self_healing_logic_anchors():
    """Verify that a logic anchor failure correctly injects context for the RetryEngine."""
    from axon.backends.base_backend import CompiledExecutionUnit, CompiledStep
    from axon.runtime.executor import Executor
    
    # Simulate a model that initially fails Syllogism but corrects itself
    mock_client = _MockSelfHealingClient(
        initial_response="The sky is blue.", # Fails Syllogism check entirely
        corrected_response="Premise: The physical scattering of light makes the sky blue. Conclusion: The sky is blue.",
        expected_violation="Premise:' and 'Conclusion:' identifiers"
    )
    
    executor = Executor(client=mock_client)  # type: ignore
    
    # Build a simple unit with the SyllogismChecker anchor
    step = CompiledStep(
        step_name="logic_test",
        system_prompt="Test",
        user_prompt="Question",
        output_schema=None,
        tool_declarations=[],
        metadata={"refine": {"max_attempts": 3, "on_exhaustion": "skip"}},
    )
    unit = CompiledExecutionUnit(
        flow_name="test_unit", 
        steps=[step],
        active_anchors=[{"name": "SyllogismChecker", "anchor_obj": SyllogismChecker}]
    )
    
    from axon.runtime.tracer import Tracer
    import asyncio
    results = asyncio.run(executor._execute_unit(unit, tracer=Tracer()))
    
    # Assert successful self-healing
    print("FAILURE CONTEXTS:", mock_client.failure_contexts)
    assert mock_client.call_count == 2
    assert "Premise:' and 'Conclusion:' identifiers" in mock_client.failure_contexts[0]
    
    # The final step result should be the corrected response that passed the anchor
    final_output = results.step_results[0].response.raw
    assert "Premise:" in final_output
    assert "Conclusion:" in final_output
