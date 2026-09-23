from d2b_core.adapters.base import (
    GenerationContext,
    HarnessAdapter,
    RefinementContext,
    VisualAnalysis,
)
from d2b_core.adapters.antigravity import AntigravityAdapter
from d2b_core.adapters.standalone import StandaloneAdapter
from d2b_core.adapters.codex import CodexAdapter
from d2b_core.adapters.claude_code import ClaudeCodeAdapter

ADAPTER_REGISTRY = {
    "antigravity": AntigravityAdapter,
    "standalone": StandaloneAdapter,
    "codex": CodexAdapter,
    "claude_code": ClaudeCodeAdapter,
}


def get_adapter(name: str = "antigravity", **kwargs) -> HarnessAdapter:
    """Instantiate a harness adapter by name."""
    cls = ADAPTER_REGISTRY.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown harness adapter: {name}. Available: {list(ADAPTER_REGISTRY.keys())}")
    return cls(**kwargs)


__all__ = [
    "HarnessAdapter",
    "VisualAnalysis",
    "GenerationContext",
    "RefinementContext",
    "AntigravityAdapter",
    "StandaloneAdapter",
    "CodexAdapter",
    "ClaudeCodeAdapter",
    "get_adapter",
]
