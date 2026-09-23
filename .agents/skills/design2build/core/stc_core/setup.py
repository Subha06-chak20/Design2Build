"""
Design2Build Intelligent Project Setup & Target Configuration Engine
=====================================================================
Performs context-aware inference from user prompts, reference images,
and workspace files to determine project targets with minimum questioning.
Generates configuration summaries and structured implementation plans.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from stc_core.config import (
    ProjectConfig,
    ProjectState,
    ProjectType,
    ReferenceIntent,
    ResponsiveMode,
    RunMode,
    TargetDevice,
)


class ProjectSetupInferrer:
    """Analyzes prompts, reference screenshots, and workspace files to infer configuration."""

    def __init__(self, workspace_dir: Optional[Union[str, Path]] = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(".")

    def infer(
        self,
        reference_path: Optional[Union[str, Path, List[Union[str, Path]]]] = None,
        prompt: Optional[str] = None,
        initial_config: Optional[ProjectConfig] = None,
    ) -> ProjectConfig:
        """Instance method for inference using configured workspace_dir."""
        refs: List[Union[str, Path]] = []
        if reference_path:
            if isinstance(reference_path, list):
                refs = reference_path
            else:
                refs = [reference_path]
        return self.infer_configuration(
            prompt_text=prompt,
            reference_paths=refs,
            workspace_dir=self.workspace_dir,
            initial_config=initial_config,
        )

    @staticmethod
    def inspect_workspace(workspace_dir: Path) -> Dict[str, Any]:
        """Detect existing framework and setup from project files."""
        inferred = {}
        pkg_json = workspace_dir / "package.json"
        
        if pkg_json.exists():
            inferred["project_state"] = ProjectState.EXISTING_PROJECT
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                if "react" in deps:
                    inferred["stack"] = "react_tailwind"
                    inferred["run_mode"] = RunMode.VITE_DEV
                elif "vue" in deps:
                    inferred["stack"] = "vue_tailwind"
                    inferred["run_mode"] = RunMode.VITE_DEV
                elif "bootstrap" in deps:
                    inferred["stack"] = "bootstrap"
            except Exception:
                pass
        elif (workspace_dir / "index.html").exists():
            inferred["project_state"] = ProjectState.EXISTING_PROJECT
            inferred["run_mode"] = RunMode.LIVE_SERVER
            
        return inferred

    @staticmethod
    def inspect_prompt(prompt_text: str) -> Dict[str, Any]:
        """Extract explicit intent, stack, device, and project type from prompt text."""
        p = prompt_text.lower()
        inferred: Dict[str, Any] = {}

        # 1. Technology / Stack
        if "react" in p:
            inferred["stack"] = "react_tailwind"
            inferred["run_mode"] = RunMode.VITE_DEV
        elif "vue" in p:
            inferred["stack"] = "vue_tailwind"
            inferred["run_mode"] = RunMode.VITE_DEV
        elif "bootstrap" in p:
            inferred["stack"] = "bootstrap"
            inferred["run_mode"] = RunMode.LIVE_SERVER
        elif "ionic" in p:
            inferred["stack"] = "ionic_tailwind"
        elif any(k in p for k in ["html", "css", "tailwind", "vanilla", "static"]):
            inferred["stack"] = "html_tailwind"
            inferred["run_mode"] = RunMode.LIVE_SERVER

        # 2. Project Type
        if "redesign" in p or "modernize" in p:
            inferred["project_type"] = ProjectType.REDESIGN
        elif "multipage" in p or "multi-page" in p:
            inferred["project_type"] = ProjectType.MULTIPAGE
        elif "landing page" in p:
            inferred["project_type"] = ProjectType.LANDING_PAGE
        elif any(k in p for k in ["ecommerce", "store", "shop", "dashboard", "portal", "web app", "webapp", "web application"]):
            inferred["project_type"] = ProjectType.WEB_APP
        elif any(k in p for k in ["prototype", "mockup", "wireframe"]):
            inferred["project_type"] = ProjectType.UI_PROTOTYPE
        elif "mobile app" in p or "ios app" in p or "android app" in p:
            inferred["project_type"] = ProjectType.MOBILE_APP
            inferred["target_devices"] = TargetDevice.MOBILE_ONLY
        elif "component" in p or "card" in p or "widget" in p:
            inferred["project_type"] = ProjectType.COMPONENT
            inferred["reference_intent"] = ReferenceIntent.COMPONENT_REFERENCE
        elif "website" in p or "site" in p:
            inferred["project_type"] = ProjectType.WEBSITE

        # 3. Target Devices & Viewports
        if any(k in p for k in ["mobile and desktop", "desktop and mobile", "mobile + desktop", "desktop + mobile"]):
            inferred["target_devices"] = TargetDevice.MOBILE_DESKTOP
            inferred["responsive_mode"] = ResponsiveMode.FULLY_RESPONSIVE
        elif any(k in p for k in ["mobile only", "phone only", "iphone only", "mobile-only"]):
            inferred["target_devices"] = TargetDevice.MOBILE_ONLY
            inferred["responsive_mode"] = ResponsiveMode.MOBILE_FOCUSED
        elif any(k in p for k in ["desktop only", "desktop-only", "large screen only"]):
            inferred["target_devices"] = TargetDevice.DESKTOP_ONLY
            inferred["responsive_mode"] = ResponsiveMode.DESKTOP_FOCUSED
        elif "tablet" in p and "desktop" not in p and "mobile" not in p:
            inferred["target_devices"] = TargetDevice.TABLET_ONLY
        elif any(k in p for k in ["all devices", "responsive", "all viewports", "every device", "fluid"]):
            inferred["target_devices"] = TargetDevice.RESPONSIVE_ALL
            inferred["responsive_mode"] = ResponsiveMode.FULLY_RESPONSIVE

        # 4. Reference Intent
        if any(k in p for k in ["exact", "pixel perfect", "recreate", "copy", "match exactly"]):
            inferred["reference_intent"] = ReferenceIntent.RECREATE_CLOSELY
        elif any(k in p for k in ["inspiration", "inspire", "similar to", "take ideas"]):
            inferred["reference_intent"] = ReferenceIntent.INSPIRATION
        elif any(k in p for k in ["component", "section only", "navbar only", "hero only"]):
            inferred["reference_intent"] = ReferenceIntent.COMPONENT_REFERENCE
        elif "design reference" in p or "style reference" in p:
            inferred["reference_intent"] = ReferenceIntent.DESIGN_REFERENCE

        # 5. Run Mode
        if "live server" in p:
            inferred["run_mode"] = RunMode.LIVE_SERVER
        elif "vite" in p:
            inferred["run_mode"] = RunMode.VITE_DEV
        elif "static" in p or "double click" in p:
            inferred["run_mode"] = RunMode.STATIC

        return inferred

    @staticmethod
    def inspect_references(reference_paths: List[Path]) -> Dict[str, Any]:
        """Analyze reference screenshot counts, names, and aspect ratios."""
        inferred: Dict[str, Any] = {}
        if not reference_paths:
            return inferred

        ref_map: Dict[str, str] = {}
        has_mobile = False
        has_desktop = False

        for r in reference_paths:
            name_lower = r.name.lower()
            if any(k in name_lower for k in ["mobile", "phone", "iphone"]):
                ref_map["mobile"] = str(r)
                has_mobile = True
            elif any(k in name_lower for k in ["desktop", "wide", "monitor", "web"]):
                ref_map["desktop"] = str(r)
                has_desktop = True

        if has_mobile and has_desktop:
            inferred["target_devices"] = TargetDevice.MOBILE_DESKTOP
            inferred["responsive_mode"] = ResponsiveMode.FULLY_RESPONSIVE
            inferred["reference_map"] = ref_map
        elif len(reference_paths) == 1:
            r = reference_paths[0]
            try:
                with Image.open(r) as img:
                    w, h = img.size
                    aspect = w / max(h, 1)
                    if aspect < 0.65:
                        inferred["target_devices"] = TargetDevice.MOBILE_ONLY
                        ref_map["mobile"] = str(r)
                    elif aspect > 1.3:
                        inferred["target_devices"] = TargetDevice.RESPONSIVE_ALL
                        ref_map["desktop"] = str(r)
            except Exception:
                pass
            inferred["reference_map"] = ref_map

        return inferred

    @classmethod
    def infer_configuration(
        cls,
        prompt_text: Optional[str] = None,
        reference_paths: Optional[List[Union[str, Path]]] = None,
        workspace_dir: Optional[Union[str, Path]] = None,
        initial_config: Optional[ProjectConfig] = None,
    ) -> ProjectConfig:
        """Combine workspace, prompt, and reference heuristics into a ProjectConfig."""
        config = initial_config or ProjectConfig()
        inferred_keys = []

        # 1. Workspace
        ws_path = Path(workspace_dir or ".")
        if ws_path.exists():
            ws_inf = cls.inspect_workspace(ws_path)
            for k, v in ws_inf.items():
                setattr(config, k, v)
                inferred_keys.append(f"workspace:{k}")

        # 2. References
        clean_refs = [Path(p) for p in (reference_paths or []) if Path(p).exists()]
        if clean_refs:
            config.reference_images = [str(p) for p in clean_refs]
            ref_inf = cls.inspect_references(clean_refs)
            for k, v in ref_inf.items():
                setattr(config, k, v)
                inferred_keys.append(f"reference:{k}")

        # 3. Prompt
        if prompt_text:
            prompt_inf = cls.inspect_prompt(prompt_text)
            for k, v in prompt_inf.items():
                setattr(config, k, v)
                inferred_keys.append(f"prompt:{k}")

        config.inferred_fields = inferred_keys
        return config


class ImplementationPlanGenerator:
    """Generates a structured implementation and verification plan based on ProjectConfig."""

    @staticmethod
    def generate_plan(config: ProjectConfig) -> str:
        """Create a 15-step custom implementation plan tailored to the confirmed configuration."""
        viewports = config.resolve_viewports()
        vp_display = ", ".join(v.title() for v in viewports)
        
        stack_titles = {
            "html_tailwind": "HTML5 + Tailwind CSS CDN + Font Awesome",
            "react_tailwind": "React 18 + Babel Standalone + Tailwind CSS",
            "vue_tailwind": "Vue 3 + Tailwind CSS",
            "bootstrap": "Bootstrap 5.3 + Bootstrap Icons",
            "ionic_tailwind": "Ionic Mobile Web Components + Tailwind CSS",
            "html_css": "Modular HTML5 + CSS + JavaScript",
        }
        stack_desc = stack_titles.get(config.stack, config.stack)

        run_instructions = {
            RunMode.LIVE_SERVER: "VS Code Live Server (open index.html) or python serve.py",
            RunMode.STATIC: "Direct browser launch without local server",
            RunMode.VITE_DEV: "Vite development server (npm run dev)",
            RunMode.EXISTING_SERVER: "Project's default development command",
        }
        run_desc = run_instructions.get(config.run_mode, str(config.run_mode))

        return f"""# IMPLEMENTATION PLAN: {config.project_type.value.replace('_', ' ').upper()}

## 1. Project Specifications
- **Technology Stack**: {stack_desc}
- **Target Devices**: {config.target_devices.value.replace('_', ' ').title()} ({vp_display})
- **Responsive Architecture**: {config.responsive_mode.value.replace('_', ' ').title()}
- **Reference Interpretation**: {config.reference_intent.value.replace('_', ' ').title()}
- **Run Mode**: {run_desc}

## 2. Milestones & Execution Stages
1. **Analyze Reference Composition**: Examine visual hierarchy, typographic scales, color palette, and component groupings.
2. **Extract Visual Assets**: Crop brand logos, photography, and icons directly into `./assets/` with outward-rounding pixel geometry.
3. **Establish Responsive Container Hierarchy**:
   - Canvas: `w-full min-h-screen`
   - Responsive Gutters: `px-4 sm:px-6 lg:px-8`
   - Max-Width Boundary: `max-w-7xl mx-auto`
4. **Scaffold Project**: Generate `{config.output_dir}` with `{config.stack}` boilerplate and asset folder.
5. **Build Major Sections**:
   - Header / Navigation Bar
   - Hero Section (2-column desktop split, stacked mobile flow)
   - Feature / Value-Proposition Grid
   - Dynamic Product / Content Cards (`grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5`)
   - Call-to-Action / Promo Banner
   - Social Proof / Reviews Strip
   - Multi-Column Responsive Footer
6. **Apply Interactive Behaviors**: Connect client-side states (modals, dropdowns, cart counters, toasts).
7. **Multi-Viewport Headless Browser Verification**:
   - Audit target viewports: {vp_display}
   - Verify zero horizontal overflow (`scrollWidth <= innerWidth`)
   - Check container fluid expansion on desktop (no narrow centered strip)
   - Ensure zero uncaught runtime JavaScript exceptions
8. **Visual Comparison & Discrepancy Diff**: Compare against reference image(s) and compute similarity score.
9. **Iterative Refinement**: Apply surgical edits to resolve any spacing, typographic, or alignment mismatches.
10. **Delivery**: Finalize files for {run_desc}.
"""
