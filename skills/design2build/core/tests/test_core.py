"""
Unit and Integration Tests for Screenshot-to-Code Core
======================================================
Tests asset cropping, preview rendering, visual comparison, scaffolding, and adapters.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from stc_core.adapters import get_adapter
from stc_core.assets import BoundingBox, crop_bounding_box, extract_and_save_asset
from stc_core.preview import PreviewRenderer, VIEWPORT_SIZES
from stc_core.project import scaffold_project
from stc_core.prompts.recipes import STACK_BOILERPLATES, get_replication_instructions
from stc_core.verification import compute_visual_difference


def create_test_image(width=1000, height=600) -> Image.Image:
    """Create a synthetic test image with known geometric shapes and colors."""
    img = Image.new("RGB", (width, height), (240, 245, 250))
    draw = ImageDraw.Draw(img)
    # Draw blue header
    draw.rectangle([0, 0, width, 80], fill=(37, 99, 235))
    # Draw red logo area in top left: (20, 20, 120, 60)
    draw.rectangle([20, 20, 120, 60], fill=(220, 38, 38))
    # Draw text/card in center
    draw.rounded_rectangle([200, 150, 800, 450], radius=16, fill=(255, 255, 255), outline=(229, 231, 235))
    return img


def test_bounding_box_and_outward_crop():
    """Test bounding box normalization and outward rounding pixel cropping."""
    img = create_test_image(1000, 600)
    
    # Target red logo: left=20, top=20, right=120, bottom=60
    # Normalized 0-1000: ymin=20/600*1000=33.3, xmin=20/1000*1000=20, ymax=60/600*1000=100, xmax=120/1000*1000=120
    box = BoundingBox(ymin=33.33, xmin=20.0, ymax=100.0, xmax=120.0)
    cropped = crop_bounding_box(img, box)

    assert cropped is not None
    # Outward rounding ensures exact or slightly generous bounds
    assert cropped.width == 100
    assert cropped.height in (40, 41)

    # Test saving asset
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "logo.png"
        src_img_path = Path(tmpdir) / "source.png"
        img.save(src_img_path)

        res = extract_and_save_asset(src_img_path, [33.33, 20.0, 100.0, 120.0], dest, name="test_logo")
        assert res is not None
        assert dest.exists()
        assert res.width == 100
        assert res.height in (40, 41)


def test_stack_recipes_and_boilerplates():
    """Test stack boilerplates and prompt generation."""
    assert "html_tailwind" in STACK_BOILERPLATES
    assert "react_tailwind" in STACK_BOILERPLATES
    assert "7.25.6" in STACK_BOILERPLATES["react_tailwind"]  # Babel 7.25.6 pinned

    prompt = get_replication_instructions(
        stack="html_tailwind",
        extracted_assets={"brand_logo": "logo.png"},
        additional_instructions="Add smooth shadow",
    )
    assert "brand_logo" in prompt
    assert "./assets/logo.png" in prompt
    assert "Add smooth shadow" in prompt


def test_adapter_registry():
    """Test harness adapter instantiation."""
    ag = get_adapter("antigravity")
    assert ag.name == "antigravity"

    st = get_adapter("standalone")
    assert st.name == "standalone"

    cx = get_adapter("codex")
    assert cx.name == "codex"

    cl = get_adapter("claude_code")
    assert cl.name == "claude_code"


def test_scaffolding():
    """Test project workspace initialization and dev server generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdir = Path(tmpdir) / "my_project"
        html = "<html><body><h1>Hello World</h1></body></html>"
        index = scaffold_project(pdir, html, stack="html_tailwind")

        assert index.exists()
        assert (pdir / "assets").exists()
        assert (pdir / "serve.py").exists()
        assert (pdir / "README.md").exists()
        assert "Hello World" in index.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_headless_browser_rendering():
    """Test headless browser screenshot capture with Playwright Chromium."""
    renderer = PreviewRenderer()
    try:
        html = """<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-blue-600 text-white p-12">
  <h1 class="text-3xl font-bold">Screenshot-to-Code Render Test</h1>
  <p class="mt-4">Testing headless Chromium visual capture.</p>
</body>
</html>"""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_png = Path(tmpdir) / "desktop.png"
            png_bytes = await renderer.capture_html(html, viewport="desktop", output_path=out_png)

            with Image.open(out_png) as img:
                assert img.size[0] == VIEWPORT_SIZES["desktop"][0]
    finally:
        await renderer.close()


def test_visual_comparator():
    """Test visual difference and similarity computation."""
    img1 = create_test_image(800, 600)
    img2 = create_test_image(800, 600)

    # Identical images
    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = Path(tmpdir) / "ref.png"
        p2 = Path(tmpdir) / "ren.png"
        p_comp = Path(tmpdir) / "comp.png"
        img1.save(p1)
        img2.save(p2)

        res_same = compute_visual_difference(p1, p2, output_composite_path=p_comp)
        assert res_same.similarity_score >= 0.99
        assert res_same.difference_percentage <= 1.0
        assert p_comp.exists()

        # Modify img2
        draw = ImageDraw.Draw(img2)
        draw.rectangle([0, 0, 800, 600], fill=(0, 0, 0))  # totally black
        img2.save(p2)

        res_diff = compute_visual_difference(p1, p2)
        assert res_diff.similarity_score < 0.5
        assert res_diff.difference_percentage > 50.0


@pytest.mark.asyncio
async def test_detect_assets_validation():
    """Test validation and error handling for automated asset detection."""
    from stc_core.assets import detect_assets_with_gemini
    img = create_test_image(400, 300)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        await detect_assets_with_gemini(img, ["logo"], api_key="")


@pytest.mark.asyncio
async def test_standalone_adapter_behavior():
    """Test StandaloneAdapter boilerplate fallback when no API key is set."""
    from stc_core.adapters import StandaloneAdapter
    from stc_core.adapters.base import GenerationContext
    adapter = StandaloneAdapter(gemini_api_key="", openai_api_key="")
    ctx = GenerationContext(
        screenshot_path=Path("dummy.png"),
        stack="html_tailwind",
    )
    code = await adapter.generate_code(ctx)
    assert "<!DOCTYPE html>" in code
    assert "tailwindcss" in code


def test_cli_doctor_and_status():
    """Test stc doctor and stc status via Click CliRunner."""
    from click.testing import CliRunner
    from stc_core.cli import cli

    runner = CliRunner()
    res_doc = runner.invoke(cli, ["doctor", "--no-check-browser"])
    assert res_doc.exit_code == 0
    assert "Design2Build Doctor" in res_doc.output
    assert "System ready" in res_doc.output

    res_stat = runner.invoke(cli, ["status"])
    assert res_stat.exit_code == 0
    assert "Design2Build Status" in res_stat.output
    assert "1.0.1" in res_stat.output



def test_responsive_prompt_directives():
    """Verify that generation prompts contain mandatory responsive layout rules."""
    instructions = get_replication_instructions(stack="html_tailwind")
    assert "max-w-7xl" in instructions
    assert "DO NOT HARDCODE SCREENSHOT DIMENSIONS" in instructions
    assert "ZERO HORIZONTAL OVERFLOW" in instructions

    from stc_core.prompts.recipes import SYSTEM_PROMPT, get_refinement_instructions
    assert "Responsive Container Hierarchy" in SYSTEM_PROMPT
    assert "Visual Specification vs. Responsive Reality" in SYSTEM_PROMPT

    refinement = get_refinement_instructions("html_tailwind", "Button is overlapping")
    assert "narrow column" in refinement
    assert "max-w-7xl" in refinement


@pytest.mark.asyncio
async def test_responsive_diagnostics_and_overflow_detection():
    """Verify headless browser responsive diagnostics and horizontal overflow detection."""
    renderer = PreviewRenderer()
    try:
        # 1. Clean fluid HTML
        fluid_html = """<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1.0"><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-50 min-h-screen">
  <div class="max-w-7xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold">Responsive Title</h1>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
      <div class="p-4 bg-white rounded shadow">Card 1</div>
      <div class="p-4 bg-white rounded shadow">Card 2</div>
      <div class="p-4 bg-white rounded shadow">Card 3</div>
      <div class="p-4 bg-white rounded shadow">Card 4</div>
    </div>
  </div>
</body>
</html>"""
        with tempfile.TemporaryDirectory() as tmpdir:
            suite = await renderer.capture_responsive_suite(fluid_html, output_dir=Path(tmpdir))
            assert len(suite) == 4
            for vp_name, diag in suite.items():
                assert not diag.has_horizontal_overflow, f"Unexpected overflow in {vp_name}"
                assert diag.is_healthy
                assert diag.screenshot_path is not None
                assert Path(diag.screenshot_path).exists()

        # 2. Defective overflowing HTML
        overflow_html = """<!DOCTYPE html>
<html>
<body style="margin: 0; padding: 0;">
  <div class="fixed-monster-box" style="width: 2500px; height: 100px; background: red;">Overflow</div>
</body>
</html>"""
        diag_overflow = await renderer.inspect_viewport_diagnostics(overflow_html, "mobile")
        assert diag_overflow.has_horizontal_overflow
        assert diag_overflow.scroll_width > diag_overflow.width
        assert not diag_overflow.is_healthy
        assert any("monster-box" in el for el in diag_overflow.overflow_elements)
    finally:
        await renderer.close()

