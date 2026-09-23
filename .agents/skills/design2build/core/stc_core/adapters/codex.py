"""
Codex Harness Adapter
=====================
Future adapter specification for OpenAI Codex / Operator agent harnesses.
"""

from pathlib import Path
from typing import Optional

from stc_core.adapters.base import (
    GenerationContext,
    HarnessAdapter,
    RefinementContext,
    VisualAnalysis,
)
from stc_core.prompts.recipes import (
    get_refinement_instructions,
    get_replication_instructions,
)


class CodexAdapter(HarnessAdapter):
    """Adapter for future OpenAI Codex / Operator agent harnesses."""

    @property
    def name(self) -> str:
        return "codex"

    async def analyze_visual(self, image_path: Path, prompt: str = "") -> VisualAnalysis:
        return VisualAnalysis(
            layout_hierarchy=["Header", "Main", "Footer"],
            suggested_stack="react_tailwind",
            raw_summary="Codex visual analysis specification.",
        )

    async def generate_code(self, context: GenerationContext) -> str:
        return get_replication_instructions(
            stack=context.stack,  # type: ignore
            extracted_assets=context.extracted_assets,
            additional_instructions=context.additional_instructions,
        )

    async def refine_code(self, context: RefinementContext) -> str:
        return get_refinement_instructions(
            current_code=context.current_code,
            discrepancies=context.discrepancy_notes,
            selected_element_html=context.selected_element_html,
        )
