"""
Design2Build Workflow Engine
============================
Orchestrates the visual coding pipeline:
1. Analyze Screenshot
2. Extract Assets
3. Scaffold Project
4. Generate Initial Code
5. Render in Browser
6. Visual Verification
7. Iterative Refinement
8. Final Packaging
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from d2b_core.adapters import HarnessAdapter, get_adapter
from d2b_core.adapters.base import GenerationContext, RefinementContext
from d2b_core.assets import ExtractedAsset, extract_assets_batch
from d2b_core.config import ProjectConfig, TargetDevice
from d2b_core.preview import PreviewRenderer
from d2b_core.project import scaffold_project
from d2b_core.prompts.recipes import STACK_BOILERPLATES, StackType
from d2b_core.verification import ComparisonResult, compute_visual_difference


@dataclass
class WorkflowStepEvent:
    step_number: int
    total_steps: int
    title: str
    details: Optional[str] = None


@dataclass
class WorkflowResult:
    success: bool
    project_dir: Path
    index_file: Path
    reference_screenshot: Path
    desktop_preview: Path
    mobile_preview: Path
    composite_diff: Optional[Path]
    similarity_score: float
    iterations_run: int
    extracted_assets: Dict[str, ExtractedAsset]


class VisualCodingWorkflow:
    """Executes the full Design2Build pipeline with a given HarnessAdapter."""

    def __init__(
        self,
        adapter: Optional[HarnessAdapter] = None,
        agent_name: str = "antigravity",
        progress_callback: Optional[Callable[[WorkflowStepEvent], None]] = None,
    ):
        self.adapter = adapter or get_adapter(agent_name)
        self.progress_callback = progress_callback
        self.renderer = PreviewRenderer()

    def _notify(self, step: int, title: str, details: Optional[str] = None):
        if self.progress_callback:
            self.progress_callback(WorkflowStepEvent(step_number=step, total_steps=8, title=title, details=details))

    async def run(
        self,
        screenshot_path: Path,
        output_dir: Path,
        stack: StackType = "html_tailwind",
        asset_boxes: Optional[List[Dict[str, Any]]] = None,
        initial_code: Optional[str] = None,
        max_refinement_passes: int = 2,
        additional_instructions: Optional[str] = None,
        config: Optional[ProjectConfig] = None,
    ) -> WorkflowResult:
        """Run the complete visual coding workflow with project target configuration."""
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = output_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        effective_stack: StackType = config.stack if (config and config.stack) else stack  # type: ignore

        try:
            # [1/8] Analyzing Screenshot
            self._notify(1, "Analyzing screenshot", f"Examining {screenshot_path.name} composition and layout")
            analysis = await self.adapter.analyze_visual(screenshot_path)

            # [2/8] Extracting Visual Assets
            self._notify(2, "Identifying and extracting visual assets", f"Cropping logos, photos, and icons")
            extracted_assets: Dict[str, ExtractedAsset] = {}
            if asset_boxes:
                extracted_assets = extract_assets_batch(screenshot_path, asset_boxes, assets_dir)
            
            asset_map = {name: asset.filename for name, asset in extracted_assets.items()}

            # [3/8] Scaffolding Project
            self._notify(3, "Preparing project workspace", f"Setting up {output_dir.name} and assets")
            code = initial_code or STACK_BOILERPLATES.get(effective_stack, STACK_BOILERPLATES["html_tailwind"])
            index_file = scaffold_project(output_dir, code, stack=effective_stack, extracted_assets=asset_map, config=config)

            # [4/8] Generating Initial Code Implementation
            self._notify(4, "Implementing UI code", f"Applying {effective_stack} design and structure")
            if not initial_code:
                gen_context = GenerationContext(
                    screenshot_path=screenshot_path,
                    stack=effective_stack,
                    extracted_assets=asset_map,
                    additional_instructions=additional_instructions,
                    project_dir=output_dir,
                    config=config,
                )
                code = await self.adapter.generate_code(gen_context)
                index_file = scaffold_project(output_dir, code, stack=effective_stack, extracted_assets=asset_map, config=config)

            # [5/8] Starting Headless Browser & Rendering Previews
            self._notify(5, "Starting browser and rendering page", "Capturing responsive preview viewports")
            desktop_preview = output_dir / "preview_desktop.png"
            mobile_preview = output_dir / "preview_mobile.png"

            # Render configured viewports if specified
            if config:
                for vp_name in config.resolve_viewports():
                    vp_out = output_dir / f"preview_{vp_name}.png"
                    await self.renderer.capture_html(code, viewport=vp_name, output_path=vp_out)
                    if vp_name in ("desktop", "desktop_wide", "large_desktop") and (not desktop_preview.exists() or vp_name == "desktop"):
                        desktop_preview = vp_out
                    if vp_name == "mobile":
                        mobile_preview = vp_out

            # Ensure primary desktop & mobile exist
            if not desktop_preview.exists():
                await self.renderer.capture_html(code, viewport="desktop", output_path=desktop_preview)
            if not mobile_preview.exists():
                await self.renderer.capture_html(code, viewport="mobile", output_path=mobile_preview)

            # Determine best comparison target (mobile if reference is vertical or mobile-only)
            compare_target = desktop_preview
            if config and config.target_devices == TargetDevice.MOBILE_ONLY:
                compare_target = mobile_preview
            else:
                from PIL import Image
                try:
                    with Image.open(screenshot_path) as ref_im:
                        if ref_im.height > ref_im.width * 1.15:
                            compare_target = mobile_preview
                except Exception:
                    pass

            # [6/8] Visual Verification
            self._notify(6, "Visual verification", f"Comparing rendered preview against {screenshot_path.name}")
            diff_path = output_dir / "diff_highlight.png"
            comp_path = output_dir / "comparison_composite.png"
            comparison = compute_visual_difference(
                reference_path=screenshot_path,
                rendered_path=compare_target,
                output_diff_path=diff_path,
                output_composite_path=comp_path,
            )

            # [7/8] Refining Implementation
            iterations = 0
            current_code = code
            while iterations < max_refinement_passes and not comparison.is_acceptable:
                iterations += 1
                self._notify(
                    7,
                    f"Refining implementation (Pass {iterations}/{max_refinement_passes})",
                    f"Similarity: {round(comparison.similarity_score * 100, 1)}% - fixing discrepancies",
                )
                
                discrepancies = (
                    f"Visual difference is {comparison.difference_percentage}%. "
                    "Check alignment, container padding, element hierarchy, typography weights, and color fidelity."
                )
                refine_context = RefinementContext(
                    screenshot_path=screenshot_path,
                    rendered_screenshot_path=compare_target,
                    current_code=current_code,
                    discrepancy_notes=discrepancies,
                    project_dir=output_dir,
                    iteration=iterations,
                    config=config,
                )
                updated_code = await self.adapter.refine_code(refine_context)
                if updated_code and updated_code != current_code:
                    current_code = updated_code
                    index_file = scaffold_project(output_dir, current_code, stack=effective_stack, extracted_assets=asset_map, config=config)
                    await self.renderer.capture_html(current_code, viewport="desktop", output_path=desktop_preview)
                    await self.renderer.capture_html(current_code, viewport="mobile", output_path=mobile_preview)
                    comparison = compute_visual_difference(
                        reference_path=screenshot_path,
                        rendered_path=compare_target,
                        output_diff_path=diff_path,
                        output_composite_path=comp_path,
                    )
                else:
                    break

            # [8/8] Final Verification & Packaging
            self._notify(8, "Final verification & packaging", f"Final similarity: {round(comparison.similarity_score * 100, 1)}%")

            return WorkflowResult(
                success=True,
                project_dir=output_dir,
                index_file=index_file,
                reference_screenshot=screenshot_path,
                desktop_preview=desktop_preview,
                mobile_preview=mobile_preview,
                composite_diff=comp_path if comp_path.exists() else None,
                similarity_score=comparison.similarity_score,
                iterations_run=iterations,
                extracted_assets=extracted_assets,
            )
        finally:
            await self.renderer.close()
