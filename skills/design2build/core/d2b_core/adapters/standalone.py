"""
Standalone API Harness Adapter
==============================
Fallback adapter that uses configured environment API keys (OpenAI, Anthropic, Gemini)
when running standalone from a terminal outside of an AI agent harness.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from d2b_core.adapters.base import (
    GenerationContext,
    HarnessAdapter,
    RefinementContext,
    VisualAnalysis,
)
from d2b_core.prompts.recipes import (
    STACK_BOILERPLATES,
    SYSTEM_PROMPT,
    get_refinement_instructions,
    get_replication_instructions,
)


class StandaloneAdapter(HarnessAdapter):
    """Adapter for running standalone via direct model API keys."""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

    @property
    def name(self) -> str:
        return "standalone"

    async def analyze_visual(self, image_path: Path, prompt: str = "") -> VisualAnalysis:
        # Default analysis
        return VisualAnalysis(
            layout_hierarchy=["Header", "Main", "Footer"],
            color_palette=["#ffffff", "#111827", "#3b82f6"],
            typography_styles=["sans-serif"],
            suggested_stack="html_tailwind",
            raw_summary="Standalone analysis using standard heuristics.",
        )

    async def generate_code(self, context: GenerationContext) -> str:
        prompt = get_replication_instructions(
            stack=context.stack,  # type: ignore
            extracted_assets=context.extracted_assets,
            additional_instructions=context.additional_instructions,
            config=context.config,
        )
        gemini_key = self.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=gemini_key)
                img_bytes = context.screenshot_path.read_bytes()
                mime = "image/png"
                if context.screenshot_path.suffix.lower() in (".jpg", ".jpeg"):
                    mime = "image/jpeg"
                response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type=mime),
                        types.Part.from_text(text=f"{SYSTEM_PROMPT}\n\n{prompt}"),
                    ],
                )
                if response.text:
                    import re
                    match = re.search(r"```(?:html)?\s*(<!DOCTYPE[\s\S]*?</html>)\s*```", response.text, re.IGNORECASE)
                    if match:
                        return match.group(1)
                    if "<!DOCTYPE" in response.text or "<html" in response.text:
                        return response.text
            except Exception as e:
                print(f"[StandaloneAdapter] API call failed: {e}, falling back to boilerplate")

        boilerplate = STACK_BOILERPLATES.get(
            context.stack, STACK_BOILERPLATES["html_tailwind"]  # type: ignore
        )
        return boilerplate

    async def refine_code(self, context: RefinementContext) -> str:
        gemini_key = self.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if gemini_key and context.rendered_screenshot_path.exists():
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=gemini_key)
                ref_bytes = context.screenshot_path.read_bytes()
                ren_bytes = context.rendered_screenshot_path.read_bytes()
                prompt = get_refinement_instructions(
                    current_code=context.current_code,
                    discrepancies=context.discrepancy_notes,
                    selected_element_html=context.selected_element_html,
                )
                response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=ref_bytes, mime_type="image/png"),
                        types.Part.from_bytes(data=ren_bytes, mime_type="image/png"),
                        types.Part.from_text(text=f"First image is reference. Second image is current rendered preview.\n\n{prompt}"),
                    ],
                )
                if response.text:
                    import re
                    match = re.search(r"```(?:html)?\s*(<!DOCTYPE[\s\S]*?</html>)\s*```", response.text, re.IGNORECASE)
                    if match:
                        return match.group(1)
                    if "<!DOCTYPE" in response.text or "<html" in response.text:
                        return response.text
            except Exception as e:
                print(f"[StandaloneAdapter] Refinement call failed: {e}")
        return context.current_code
