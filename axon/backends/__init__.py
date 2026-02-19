# AXON Backends — Model-specific prompt compilers
# IR → Backend-specific prompt structures
#
# Each backend implements BaseBackend to compile AXON IR
# into provider-native formats (Claude, Gemini, OpenAI, etc.)

from .base_backend import (
    BaseBackend,
    CompiledProgram,
    CompiledExecutionUnit,
    CompiledStep,
    CompilationContext,
)
from .anthropic_backend import AnthropicBackend
from .gemini_backend import GeminiBackend
from .openai_backend import OpenAIBackend
from .ollama_backend import OllamaBackend

# Backend registry — maps canonical names to backend classes
BACKEND_REGISTRY: dict[str, type[BaseBackend]] = {
    "anthropic": AnthropicBackend,
    "gemini": GeminiBackend,
    "openai": OpenAIBackend,
    "ollama": OllamaBackend,
}


def get_backend(name: str) -> BaseBackend:
    """
    Get a backend instance by canonical name.

    Raises:
        ValueError: If the backend name is not recognized.
    """
    if name not in BACKEND_REGISTRY:
        available = ", ".join(sorted(BACKEND_REGISTRY.keys()))
        raise ValueError(
            f"Unknown backend '{name}'. Available: {available}"
        )
    return BACKEND_REGISTRY[name]()
