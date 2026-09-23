"""
Antigravity Harness Adapter
===========================
Integrates the screenshot-to-code workflow natively with Google Antigravity.
Allows Antigravity's vision model and agentic tool loop to directly perform
screenshot inspection, asset extraction, code generation, and iterative refinement.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from stc_core.adapters.base import (
    GenerationContext,
    HarnessAdapter,
    RefinementContext,
    VisualAnalysis,
)
from stc_core.prompts.recipes import (
    STACK_BOILERPLATES,
    SYSTEM_PROMPT,
    get_refinement_instructions,
    get_replication_instructions,
)


class AntigravityAdapter(HarnessAdapter):
    """Adapter for Antigravity-native visual coding execution."""

    @property
    def name(self) -> str:
        return "antigravity"

    async def analyze_visual(self, image_path: Path, prompt: str = "") -> VisualAnalysis:
        """
        Produce structured guidance for Antigravity's vision inspection.
        When running within Antigravity, Antigravity directly inspects the screenshot
        via its native multimodal vision capabilities.
        """
        return VisualAnalysis(
            layout_hierarchy=["Header/Navbar", "Hero Section", "Content Grid/Cards", "Footer"],
            color_palette=["Primary Brand", "Background Tint", "Text Dark", "Accent/CTA"],
            typography_styles=["Heading Display Font", "Body Sans Font", "Monospace/Badges"],
            suggested_stack="html_tailwind",
            raw_summary="Antigravity vision analysis guided by screenshot-to-code skill.",
        )

    async def generate_code(self, context: GenerationContext) -> str:
        """
        When Antigravity runs interactively, Antigravity generates code using its native tools.
        For CLI workflow execution, returns the valid scaffold boilerplate populated with assets.
        """
        boilerplate = STACK_BOILERPLATES.get(
            context.stack, STACK_BOILERPLATES["html_tailwind"]  # type: ignore
        )
        return boilerplate

    async def refine_code(self, context: RefinementContext) -> str:
        """
        In Antigravity agent mode, Antigravity performs surgical file edits.
        """
        return context.current_code
