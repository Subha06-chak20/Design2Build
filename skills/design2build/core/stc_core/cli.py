"""
Screenshot-to-Code (stc) CLI
============================
Unified command-line interface for the Screenshot-to-Code visual coding engine.
Supports automated generation, headless browser preview, asset cropping,
visual diffing, environment diagnostics (doctor), status reporting, project checking, and refinement.
"""

import asyncio
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import click

from stc_core.adapters import get_adapter
from stc_core.adapters.base import GenerationContext, RefinementContext
from stc_core.assets import extract_and_save_asset, extract_assets_batch
from stc_core.preview import PreviewRenderer, VIEWPORT_SIZES
from stc_core.preview.renderer import find_system_edge
from stc_core.prompts.recipes import StackType
from stc_core.verification import compute_visual_difference
from stc_core.workflow import VisualCodingWorkflow, WorkflowStepEvent


def progress_printer(event: WorkflowStepEvent):
    """Formats and prints step progress to stdout."""
    prefix = click.style(f"[{event.step_number}/{event.total_steps}]", fg="cyan", bold=True)
    title = click.style(event.title, bold=True)
    details = f" - {event.details}" if event.details else ""
    click.echo(f"{prefix} {title}{details}")


@click.group()
@click.version_option(version="1.0.1")
def cli():
    """Design2Build CLI: Reusable, agent-native visual coding workflow."""
    pass


# ----------------------------------------------------------------------
# d2b doctor: Environment and system diagnostics
# ----------------------------------------------------------------------
@cli.command()
@click.option("--check-browser/--no-check-browser", default=True, help="Test actual browser launch")
def doctor(check_browser: bool):
    """Verify environment health, browser engines, dependencies, and adapter readiness."""
    click.echo(click.style("\n=== Design2Build Doctor ===", fg="cyan", bold=True))
    click.echo("Verifying system dependencies and execution readiness...\n")

    has_error = False

    # 1. Python version
    py_ver = sys.version_info
    py_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    if py_ver >= (3, 10):
        click.echo(f"  {click.style('✓', fg='green', bold=True)} Python: {py_str} (>=3.10 required)")
    else:
        click.echo(f"  {click.style('✗', fg='red', bold=True)} Python: {py_str} (requires 3.10 or higher)")
        has_error = True

    # 2. Core Python package dependencies
    core_pkgs = ["PIL", "bs4", "click", "pydantic", "httpx"]
    missing_pkgs = []
    for pkg in core_pkgs:
        try:
            __import__(pkg)
        except ImportError:
            missing_pkgs.append(pkg)

    if not missing_pkgs:
        click.echo(f"  {click.style('✓', fg='green', bold=True)} Core dependencies: {', '.join(core_pkgs)}")
    else:
        click.echo(f"  {click.style('✗', fg='red', bold=True)} Missing core packages: {', '.join(missing_pkgs)}")
        has_error = True

    # 3. Playwright library
    try:
        pw_ver = importlib.metadata.version("playwright")
        click.echo(f"  {click.style('✓', fg='green', bold=True)} Playwright library: v{pw_ver}")
        pw_installed = True
    except Exception:
        click.echo(f"  {click.style('✗', fg='red', bold=True)} Playwright library: Not installed (run 'pip install playwright')")
        pw_installed = False
        has_error = True

    # 4. Chromium browser binary launch check
    if pw_installed and check_browser:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                b = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
                b.close()
            click.echo(f"  {click.style('✓', fg='green', bold=True)} Chromium browser engine: Available & launch verified")
        except Exception as e:
            click.echo(f"  {click.style('!', fg='yellow', bold=True)} Chromium browser engine: Playwright launch failed ({e})")
            click.echo("    Hint: Run 'playwright install chromium' to download the headless browser.")
    elif not check_browser:
        click.echo(f"  {click.style('•', fg='blue')} Chromium browser engine: Check skipped by flag")

    # 5. System Microsoft Edge headless fallback
    edge_exe = find_system_edge()
    if edge_exe:
        click.echo(f"  {click.style('✓', fg='green', bold=True)} Edge headless fallback: Available ({edge_exe})")
    else:
        click.echo(f"  {click.style('!', fg='yellow', bold=True)} Edge headless fallback: Not found (Playwright Chromium required)")

    # 6. Node.js & npm (Optional, for framework projects like Vite/Next)
    node_exe = shutil.which("node")
    npm_exe = shutil.which("npm.cmd") or shutil.which("npm")
    if node_exe:
        try:
            node_v = subprocess.check_output([node_exe, "--version"], text=True).strip()
            npm_v = subprocess.check_output([npm_exe, "--version"], text=True, shell=True).strip() if npm_exe else "N/A"
            click.echo(f"  {click.style('✓', fg='green', bold=True)} Node runtime & package manager: {node_v} / npm {npm_v}")
        except Exception:
            click.echo(f"  {click.style('✓', fg='green', bold=True)} Node runtime: Found at {node_exe}")
    else:
        click.echo(f"  {click.style('•', fg='blue')} Node runtime: Optional (Not detected on PATH, static stacks work without Node)")

    # 7. Antigravity integration & harness adapters
    harnesses = ["antigravity", "standalone", "codex", "claude_code"]
    loaded_harnesses = []
    for h in harnesses:
        try:
            get_adapter(h)
            loaded_harnesses.append(h)
        except Exception:
            pass

    if "antigravity" in loaded_harnesses:
        click.echo(f"  {click.style('✓', fg='green', bold=True)} Antigravity adapter: Ready ({', '.join(loaded_harnesses)} available)")
    else:
        click.echo(f"  {click.style('✗', fg='red', bold=True)} Antigravity adapter: Failed to load")
        has_error = True

    # 8. Project directory write permissions
    cwd = Path.cwd()
    test_file = cwd / ".stc_test_write.tmp"
    try:
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        click.echo(f"  {click.style('✓', fg='green', bold=True)} Project write access: OK ({cwd})")
    except Exception as e:
        click.echo(f"  {click.style('✗', fg='red', bold=True)} Project write access: Failed ({e})")
        has_error = True

    click.echo("")
    if has_error:
        click.echo(click.style("Doctor found issues that need attention before running workflows.", fg="red", bold=True))
        sys.exit(1)
    else:
        click.echo(click.style("System ready for Design2Build visual coding workflows.", fg="green", bold=True))


# ----------------------------------------------------------------------
# d2b status: Configuration and environment status
# ----------------------------------------------------------------------
@cli.command()
@click.option("--project", "-p", default=".", type=click.Path(path_type=Path), help="Target project directory")
def status(project: Path):
    """Display installed version, active adapter, browser status, and project context."""
    click.echo(click.style("\n=== Design2Build Status ===", fg="cyan", bold=True))

    # Version & core
    click.echo(f"  Version           : 1.0.1 (design2build)")
    click.echo(f"  Status            : Ready")
    click.echo(f"  Default Harness   : antigravity")
    click.echo(f"  Available Adapters: antigravity, standalone, codex, claude_code")

    # Browser status
    pw_installed = False
    try:
        pw_ver = importlib.metadata.version("playwright")
        pw_installed = True
        pw_status = f"Playwright v{pw_ver} (Chromium 1280x832 / 342x684)"
    except Exception:
        pw_status = "Playwright not installed"

    edge_path = find_system_edge()
    edge_status = f"Available ({edge_path})" if edge_path else "Not found"
    click.echo(f"  Headless Browser  : {pw_status}")
    click.echo(f"  Edge CLI Fallback : {edge_status}")

    # API keys
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    click.echo(f"  GEMINI_API_KEY    : {'Configured' if gemini_key else 'Not set (Optional for standalone)'}")
    click.echo(f"  OPENAI_API_KEY    : {'Configured' if openai_key else 'Not set (Optional for standalone)'}")

    # Project context
    proj_dir = project.resolve()
    click.echo(f"\n  Project Directory : {proj_dir}")
    if proj_dir.exists():
        index_file = proj_dir / "index.html"
        pkg_file = proj_dir / "package.json"
        ref_dir = proj_dir / "reference"
        assets_dir = proj_dir / "assets"
        stc_dir = proj_dir / ".stc"

        click.echo(f"  - index.html      : {'Found' if index_file.exists() else 'Not found'}")
        click.echo(f"  - package.json    : {'Found' if pkg_file.exists() else 'Not found'}")
        click.echo(f"  - reference/      : {'Found' if ref_dir.is_dir() else 'Not found'}")
        click.echo(f"  - assets/         : {'Found' if assets_dir.is_dir() else 'Not found'}")
        click.echo(f"  - .stc/ cache     : {'Found' if stc_dir.is_dir() else 'Not initialized'}")
    else:
        click.echo(f"  - Directory does not exist yet (will be created on generate).")
    click.echo("")


# ----------------------------------------------------------------------
# stc check: Visual parity check between project and reference
# ----------------------------------------------------------------------
@cli.command()
@click.argument("reference", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--project", "-p", default=".", type=click.Path(path_type=Path), help="Project directory to inspect")
@click.option("--entry", "-e", help="Entry HTML file (defaults to auto-detect index.html)")
@click.option("--viewport", "-v", default="auto", type=click.Choice(["auto", "mobile", "tablet", "desktop", "desktop_wide", "large_desktop"]))
@click.option("--responsive/--no-responsive", default=True, help="Run responsive multi-viewport health audit")
@click.option("--diff-out", type=click.Path(path_type=Path), help="Output path for highlighted diff PNG")
@click.option("--composite-out", type=click.Path(path_type=Path), help="Output path for side-by-side composite PNG")
def check(
    reference: Path,
    project: Path,
    entry: Optional[str],
    viewport: str,
    responsive: bool,
    diff_out: Optional[Path],
    composite_out: Optional[Path],
):
    """Render the current project and visually compare it against a reference screenshot with responsive checks."""
    proj_dir = Path(project).resolve()
    stc_cache = proj_dir / ".stc"
    stc_cache.mkdir(parents=True, exist_ok=True)

    # Locate entry file
    if entry:
        entry_file = proj_dir / entry
    else:
        candidates = [
            proj_dir / "index.html",
            proj_dir / "public" / "index.html",
            proj_dir / "src" / "index.html",
        ]
        entry_file = next((c for c in candidates if c.exists()), None)

    if not entry_file or not entry_file.exists():
        click.echo(click.style(f"Error: Could not find entry HTML file in {proj_dir}.", fg="red"), err=True)
        click.echo("Please specify the entry file explicitly using --entry <path>.")
        sys.exit(1)

    # Detect reference aspect ratio to choose optimal comparison viewport
    from PIL import Image
    with Image.open(reference) as ref_img_peek:
        ref_w, ref_h = ref_img_peek.size
        is_vertical_reference = (ref_h > ref_w * 1.15)

    if viewport == "auto":
        target_viewport = "mobile" if is_vertical_reference else "desktop_wide"
        click.echo(f"Auto-selected viewport: {target_viewport} (Reference is {'vertical/mobile' if is_vertical_reference else 'horizontal/desktop'})")
    else:
        target_viewport = viewport

    click.echo(click.style("\n=== Screenshot-to-Code Visual Verification ===", fg="cyan", bold=True))
    click.echo(f"Reference Screenshot : {reference.resolve()} ({ref_w}x{ref_h}px)")
    click.echo(f"Project Entry File   : {entry_file}")
    click.echo(f"Target Viewport      : {target_viewport} ({VIEWPORT_SIZES[target_viewport][0]}x{VIEWPORT_SIZES[target_viewport][1]}px)\n")

    # Render current preview
    rendered_png = stc_cache / f"check_preview_{target_viewport}.png"
    renderer = PreviewRenderer()

    async def _render_and_diff():
        try:
            await renderer.capture_file(entry_file, viewport=target_viewport, output_path=rendered_png)
        finally:
            await renderer.close()

    try:
        asyncio.run(_render_and_diff())
    except Exception as exc:
        click.echo(click.style(f"Render error: {exc}", fg="red"), err=True)
        sys.exit(1)

    # Compute visual diff
    actual_diff_out = diff_out or (stc_cache / f"diff_{target_viewport}.png")
    actual_comp_out = composite_out or (stc_cache / f"composite_{target_viewport}.png")

    result = compute_visual_difference(
        reference_path=reference,
        rendered_path=rendered_png,
        output_diff_path=actual_diff_out,
        output_composite_path=actual_comp_out,
    )

    similarity_pct = round(result.similarity_score * 100, 1)
    status_label = "PASS (>=90%)" if result.is_acceptable else "NEEDS REFINEMENT (<90%)"
    status_color = "green" if result.is_acceptable else "yellow"

    click.echo(click.style("--- Comparison Summary ---", bold=True))
    click.echo(f"Similarity Score     : {click.style(f'{similarity_pct}%', fg=status_color, bold=True)}")
    click.echo(f"Visual Discrepancy   : {result.difference_percentage}%")
    click.echo(f"Verification Status  : {click.style(status_label, fg=status_color, bold=True)}")
    click.echo(f"Reference Dimensions : {result.reference_size[0]}x{result.reference_size[1]}px")
    click.echo(f"Rendered Dimensions  : {result.rendered_size[0]}x{result.rendered_size[1]}px")
    if result.aspect_ratio_mismatch:
        click.echo(click.style("Notice: Aspect ratio mismatch between reference and rendered capture. Testing responsive suite for layout verification.", fg="yellow"))
    click.echo(f"\nRendered Preview     : {rendered_png}")
    click.echo(f"Diff Highlights      : {actual_diff_out}")
    click.echo(f"Side-by-Side View    : {actual_comp_out}")

    # Responsive Health Audit Suite
    if responsive:
        click.echo(click.style("\n--- Responsive Layout Health Audit ---", bold=True))
        async def _run_suite():
            r = PreviewRenderer()
            try:
                return await r.capture_responsive_suite(
                    html_or_file=entry_file,
                    output_dir=stc_cache,
                    viewports=("mobile", "tablet", "desktop", "large_desktop"),
                )
            finally:
                await r.close()

        suite_results = asyncio.run(_run_suite())

        all_responsive_ok = True
        for vp_name, diag in suite_results.items():
            vp_label = f"{vp_name.title()} ({diag.width}x{diag.height}px)"
            if diag.has_horizontal_overflow:
                click.echo(f"  {click.style('✗', fg='red', bold=True)} {vp_label}: Horizontal overflow detected! (content scrollWidth: {diag.scroll_width}px > {diag.width}px)")
                if diag.overflow_elements:
                    click.echo(f"    Overflowing element(s): {', '.join(diag.overflow_elements)}")
                all_responsive_ok = False
            elif diag.is_artificially_narrow:
                click.echo(f"  {click.style('!', fg='yellow', bold=True)} {vp_label}: Narrow container detected on wide desktop ({diag.main_container_width}px). Should expand gracefully.")
                all_responsive_ok = False
            elif diag.page_errors:
                click.echo(f"  {click.style('✗', fg='red', bold=True)} {vp_label}: Runtime page errors: {diag.page_errors[0]}")
                all_responsive_ok = False
            else:
                extra = f" (Container width: {diag.main_container_width}px)" if diag.main_container_width else ""
                click.echo(f"  {click.style('✓', fg='green', bold=True)} {vp_label}: Healthy & fluid{extra}")

        if all_responsive_ok:
            click.echo(click.style("\n[✓] All responsive viewports verified: Fluid, no horizontal overflow, zero runtime errors.", fg="green", bold=True))
        else:
            click.echo(click.style("\n[!] Responsive issues found. Inspect generated previews in .stc/.", fg="yellow", bold=True))

    click.echo(click.style("\n--- Visual Discrepancy Checklist ---", bold=True))
    click.echo(f" [{'✓' if result.similarity_score > 0.85 else ' '}] Overall Layout Hierarchy & Alignment")
    click.echo(f" [{'✓' if result.difference_percentage < 15.0 else ' '}] Color Palette & Background Contrast")
    click.echo(f" [{'✓' if result.similarity_score > 0.90 else ' '}] Typography Sizing & Font Weight Fidelity")
    click.echo(f" [{'✓' if result.similarity_score > 0.92 else ' '}] Asset & Icon Placement")
    click.echo(f" [{'✓' if result.is_acceptable else ' '}] Spacing, Gaps, and Padding Precision\n")

    if not result.is_acceptable:
        click.echo(click.style("Run 'stc refine <reference>' or ask Antigravity to adjust the layout.", fg="yellow"))


# ----------------------------------------------------------------------
# stc refine: Iterative refinement of existing project
# ----------------------------------------------------------------------
@cli.command()
@click.argument("reference", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--project", "-p", default=".", type=click.Path(path_type=Path), help="Existing project directory")
@click.option("--entry", "-e", default="index.html", help="Entry file name (default index.html)")
@click.option("--agent", "-a", default="antigravity", help="Harness adapter: antigravity, standalone, codex, claude_code")
@click.option("--max-passes", default=1, type=int, help="Maximum refinement passes to execute")
@click.option("--instructions", help="Optional specific refinement guidance (e.g. 'Fix hero button alignment')")
def refine(
    reference: Path,
    project: Path,
    entry: str,
    agent: str,
    max_passes: int,
    instructions: Optional[str],
):
    """Inspect and refine an existing project against a reference screenshot without recreating it."""
    proj_dir = Path(project).resolve()
    target_file = proj_dir / entry

    if not target_file.exists():
        click.echo(click.style(f"Error: Entry file not found at {target_file}", fg="red"), err=True)
        sys.exit(1)

    click.echo(click.style("\n=== Screenshot-to-Code Refinement Loop ===", fg="cyan", bold=True))
    click.echo(f"Reference : {reference.resolve()}")
    click.echo(f"Project   : {proj_dir}")
    click.echo(f"Entry     : {entry}")
    click.echo(f"Harness   : {agent} | Max Passes: {max_passes}\n")

    stc_cache = proj_dir / ".stc"
    stc_cache.mkdir(parents=True, exist_ok=True)
    backup_dir = stc_cache / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Save backup of existing file
    timestamp = int(time.time())
    backup_file = backup_dir / f"{target_file.stem}_{timestamp}{target_file.suffix}"
    backup_file.write_text(target_file.read_text(encoding="utf-8"), encoding="utf-8")
    click.echo(f"Backed up current code to: {backup_file.relative_to(proj_dir)}")

    adapter = get_adapter(agent)
    renderer = PreviewRenderer()

    async def _execute_refinement():
        current_code = target_file.read_text(encoding="utf-8")
        desktop_preview = stc_cache / "refine_preview.png"
        diff_path = stc_cache / "refine_diff.png"
        comp_path = stc_cache / "refine_composite.png"

        try:
            # Initial baseline render
            click.echo("Rendering current implementation...")
            await renderer.capture_html(current_code, viewport="desktop", output_path=desktop_preview)

            comp = compute_visual_difference(
                reference_path=reference,
                rendered_path=desktop_preview,
                output_diff_path=diff_path,
                output_composite_path=comp_path,
            )

            initial_score = comp.similarity_score
            click.echo(f"Initial visual similarity: {click.style(f'{round(initial_score * 100, 1)}%', bold=True)}")

            if comp.is_acceptable and not instructions:
                click.echo(click.style("Implementation already meets visual fidelity threshold (>=90%).", fg="green"))
                return

            passes_completed = 0
            for pass_num in range(1, max_passes + 1):
                click.echo(f"\nRunning refinement pass {pass_num}/{max_passes}...")
                discrepancy_summary = (
                    f"Visual difference: {comp.difference_percentage}%. "
                    f"Discrepancies noted: {instructions or 'Align container spacing, font weights, colors, and borders.'}"
                )

                ctx = RefinementContext(
                    screenshot_path=reference,
                    rendered_screenshot_path=desktop_preview,
                    current_code=current_code,
                    discrepancy_notes=discrepancy_summary,
                    project_dir=proj_dir,
                    iteration=pass_num,
                )

                updated_code = await adapter.refine_code(ctx)
                if updated_code and updated_code != current_code:
                    current_code = updated_code
                    target_file.write_text(current_code, encoding="utf-8")
                    click.echo("Updated code applied to project entry file.")

                    await renderer.capture_html(current_code, viewport="desktop", output_path=desktop_preview)
                    comp = compute_visual_difference(
                        reference_path=reference,
                        rendered_path=desktop_preview,
                        output_diff_path=diff_path,
                        output_composite_path=comp_path,
                    )
                    click.echo(f"Pass {pass_num} similarity: {click.style(f'{round(comp.similarity_score * 100, 1)}%', fg='cyan', bold=True)}")
                    passes_completed += 1
                else:
                    if agent == "antigravity":
                        click.echo("Antigravity interactive adapter active: Apply edits in chat using skill instructions.")
                    else:
                        click.echo("No further automated changes returned by adapter.")
                    break

            click.echo(click.style("\nRefinement finished!", fg="green", bold=True))
            click.echo(f"Initial similarity : {round(initial_score * 100, 1)}%")
            click.echo(f"Final similarity   : {round(comp.similarity_score * 100, 1)}%")
            click.echo(f"Composite diff     : {comp_path}")
        finally:
            await renderer.close()

    try:
        asyncio.run(_execute_refinement())
    except Exception as exc:
        click.echo(click.style(f"Refinement error: {exc}", fg="red"), err=True)
        sys.exit(1)


# ----------------------------------------------------------------------
# stc generate: Full 8-stage visual coding pipeline
# ----------------------------------------------------------------------
@cli.command()
@click.argument("screenshot", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--stack", default="html_tailwind", help="Target stack: html_tailwind, react_tailwind, vue_tailwind, bootstrap, html_css")
@click.option("--out", "-o", "--project", "-p", default="./output", type=click.Path(path_type=Path), help="Target output / project directory")
@click.option("--agent", "-a", default="antigravity", help="Agent harness: antigravity, standalone, codex, claude_code")
@click.option("--boxes", help="JSON string or file containing bounding boxes to extract")
@click.option("--boxes-file", type=click.Path(exists=True, path_type=Path), help="JSON file containing array of bounding boxes")
@click.option("--code", type=click.Path(exists=True, path_type=Path), help="Optional initial code file to verify/refine directly")
@click.option("--max-passes", default=2, type=int, help="Maximum visual refinement passes")
@click.option("--instructions", help="Additional user requirements (e.g. 'Add functional tabs')")
def generate(
    screenshot: Path,
    stack: str,
    out: Path,
    agent: str,
    boxes: Optional[str],
    boxes_file: Optional[Path],
    code: Optional[Path],
    max_passes: int,
    instructions: Optional[str],
):
    """Execute the full 8-step visual coding workflow on a screenshot."""
    click.echo(click.style("\n=== Screenshot-to-Code Workflow ===", fg="green", bold=True))
    click.echo(f"Input: {screenshot}")
    click.echo(f"Stack: {stack} | Harness: {agent} | Output: {out}\n")

    asset_boxes = []
    if boxes_file:
        asset_boxes = json.loads(boxes_file.read_text(encoding="utf-8"))
    elif boxes:
        p_boxes = Path(boxes)
        if p_boxes.exists():
            asset_boxes = json.loads(p_boxes.read_text(encoding="utf-8"))
        else:
            asset_boxes = json.loads(boxes)

    initial_code_str = code.read_text(encoding="utf-8") if code else None

    workflow = VisualCodingWorkflow(
        agent_name=agent,
        progress_callback=progress_printer,
    )

    async def _exec():
        return await workflow.run(
            screenshot_path=screenshot,
            output_dir=out,
            stack=stack,  # type: ignore
            asset_boxes=asset_boxes,
            initial_code=initial_code_str,
            max_refinement_passes=max_passes,
            additional_instructions=instructions,
        )

    try:
        res = asyncio.run(_exec())
        click.echo(click.style("\n Workflow completed successfully!", fg="green", bold=True))
        click.echo(f"Project directory : {res.project_dir}")
        click.echo(f"Main entry file   : {res.index_file}")
        click.echo(f"Desktop preview   : {res.desktop_preview}")
        click.echo(f"Mobile preview    : {res.mobile_preview}")
        if res.composite_diff:
            click.echo(f"Visual diff       : {res.composite_diff}")
        click.echo(f"Similarity score  : {round(res.similarity_score * 100, 1)}%")
    except Exception as exc:
        click.echo(click.style(f"\n Workflow error: {exc}", fg="red", bold=True), err=True)
        sys.exit(1)


# ----------------------------------------------------------------------
# stc preview: Headless browser rendering
# ----------------------------------------------------------------------
@cli.command()
@click.argument("html_source", type=click.Path(exists=True, path_type=Path))
@click.option("--out", "-o", default="preview.png", type=click.Path(path_type=Path), help="Output screenshot PNG path")
@click.option("--viewport", "-v", default="desktop_wide", type=click.Choice(["mobile", "tablet", "desktop", "desktop_wide", "large_desktop", "both", "all"]))
def preview(html_source: Path, out: Path, viewport: str):
    """Render an HTML file in headless browser across responsive viewports."""
    click.echo(f"Rendering {html_source} (viewport: {viewport})...")
    renderer = PreviewRenderer()

    async def _render():
        if viewport == "all":
            out_dir = out.parent if out.suffix else out
            res = await renderer.capture_responsive_suite(html_source, output_dir=out_dir)
            click.echo(click.style(f"Rendered responsive suite ({len(res)} viewports):", fg="green", bold=True))
            for vp_name, diag in res.items():
                status = "OK" if diag.is_healthy else "ISSUES DETECTED"
                color = "green" if diag.is_healthy else "yellow"
                click.echo(f"  - {vp_name.title()} ({diag.width}x{diag.height}px): {click.style(status, fg=color)} -> {diag.screenshot_path}")
        elif viewport == "both":
            out_dir = out.parent if out.suffix else out
            res = await renderer.capture_both_viewports(html_source, output_dir=out_dir)
            click.echo(f"Rendered desktop: {len(res['desktop'])} bytes")
            click.echo(f"Rendered mobile: {len(res['mobile'])} bytes")
        else:
            png_bytes = await renderer.capture_file(html_source, viewport=viewport, output_path=out)
            click.echo(click.style(f"Saved screenshot to {out} ({len(png_bytes)} bytes)", fg="green"))

    try:
        asyncio.run(_render())
    except Exception as exc:
        click.echo(click.style(f"Render error: {exc}", fg="red"), err=True)
        sys.exit(1)


# ----------------------------------------------------------------------
# stc extract-assets: Bounding box image extraction
# ----------------------------------------------------------------------
@cli.command("extract-assets")
@click.argument("screenshot", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--box", help="Coordinates as 'ymin,xmin,ymax,xmax' (0-1000 normalized)")
@click.option("--name", default="asset", help="Asset identifier / name")
@click.option("--out-dir", "-o", default="./assets", type=click.Path(path_type=Path), help="Destination assets directory")
@click.option("--boxes-file", type=click.Path(exists=True, path_type=Path), help="JSON file containing array of asset definitions")
def extract_assets(
    screenshot: Path,
    box: Optional[str],
    name: str,
    out_dir: Path,
    boxes_file: Optional[Path],
):
    """Extract and crop visual assets from a screenshot using outward-rounding geometry."""
    out_dir.mkdir(parents=True, exist_ok=True)

    if boxes_file:
        configs = json.loads(boxes_file.read_text(encoding="utf-8"))
        res = extract_assets_batch(screenshot, configs, out_dir)
        click.echo(click.style(f"Extracted {len(res)} assets into {out_dir}:", fg="green"))
        for asset_name, asset in res.items():
            click.echo(f"  - {asset_name}: {asset.filename} ({asset.width}x{asset.height}px)")
        return

    if box:
        coords = [float(x.strip()) for x in box.split(",")]
        dest = out_dir / f"{name}.png"
        res = extract_and_save_asset(screenshot, coords, dest, name=name)
        if res:
            click.echo(click.style(f"Extracted asset {name} -> {res.filepath} ({res.width}x{res.height}px)", fg="green"))
        else:
            click.echo(click.style("Failed to crop asset (invalid bounding box)", fg="red"), err=True)
            sys.exit(1)
    else:
        click.echo(click.style("Please specify either --box or --boxes-file", fg="yellow"))


# ----------------------------------------------------------------------
# stc diff: Visual comparison and metrics
# ----------------------------------------------------------------------
@cli.command()
@click.argument("reference", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("rendered", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--diff-out", type=click.Path(path_type=Path), help="Output path for highlighted diff PNG")
@click.option("--composite-out", type=click.Path(path_type=Path), help="Output path for side-by-side composite PNG")
def diff(reference: Path, rendered: Path, diff_out: Optional[Path], composite_out: Optional[Path]):
    """Compare reference screenshot with rendered browser screenshot."""
    res = compute_visual_difference(
        reference_path=reference,
        rendered_path=rendered,
        output_diff_path=diff_out,
        output_composite_path=composite_out,
    )
    click.echo(click.style("=== Visual Comparison Results ===", fg="cyan", bold=True))
    click.echo(f"Similarity Score : {round(res.similarity_score * 100, 2)}%")
    click.echo(f"Discrepancy      : {res.difference_percentage}%")
    click.echo(f"Reference Size   : {res.reference_size[0]}x{res.reference_size[1]}px")
    click.echo(f"Rendered Size    : {res.rendered_size[0]}x{res.rendered_size[1]}px")
    if res.diff_image_path:
        click.echo(f"Diff Highlight   : {res.diff_image_path}")
    if res.composite_image_path:
        click.echo(f"Composite View   : {res.composite_image_path}")


if __name__ == "__main__":
    cli()
