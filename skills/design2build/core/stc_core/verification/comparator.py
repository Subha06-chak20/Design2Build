"""
Visual Verification and Comparison Engine
=========================================
Computes perceptual visual similarity between reference and rendered screenshots,
generates side-by-side comparison images, and constructs structured verification reports.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from PIL import Image, ImageChops, ImageDraw, ImageOps
from pydantic import BaseModel


class ComparisonResult(BaseModel):
    similarity_score: float  # 0.0 (completely different) to 1.0 (identical)
    difference_percentage: float  # 0.0% to 100.0%
    reference_size: Tuple[int, int]
    rendered_size: Tuple[int, int]
    aspect_ratio_mismatch: bool = False
    composite_image_path: Optional[str] = None
    diff_image_path: Optional[str] = None
    is_acceptable: bool = False


def compute_visual_difference(
    reference_path: Union[str, Path],
    rendered_path: Union[str, Path],
    output_diff_path: Optional[Union[str, Path]] = None,
    output_composite_path: Optional[Union[str, Path]] = None,
    acceptable_threshold: float = 0.88,
) -> ComparisonResult:
    """Compare reference screenshot against rendered screenshot."""
    ref_img = Image.open(reference_path).convert("RGB")
    ren_img = Image.open(rendered_path).convert("RGB")

    ref_size = ref_img.size
    ren_size = ren_img.size

    # Check for significant aspect ratio mismatch (e.g. mobile vertical screenshot vs widescreen desktop render)
    ref_aspect = ref_size[0] / max(1, ref_size[1])
    ren_aspect = ren_size[0] / max(1, ren_size[1])
    aspect_mismatch = abs(ref_aspect - ren_aspect) > 0.35

    # Normalize rendered image to reference image dimensions for pixel comparison
    if ref_size != ren_size:
        ren_img_aligned = ren_img.resize(ref_size, Image.Resampling.LANCZOS)
    else:
        ren_img_aligned = ren_img

    # Pixel difference
    diff = ImageChops.difference(ref_img, ren_img_aligned)
    
    # Calculate difference percentage
    stat = diff.convert("L").getextrema()
    # RMS difference
    import math
    h = diff.histogram()
    sq = (value * ((idx % 256) ** 2) for idx, value in enumerate(h))
    sum_of_squares = sum(sq)
    rms = math.sqrt(sum_of_squares / float(ref_size[0] * ref_size[1] * 3))
    
    # Normalize rms: 0 is identical, 255 is inverted
    similarity_score = max(0.0, min(1.0, 1.0 - (rms / 128.0)))
    diff_percentage = round((1.0 - similarity_score) * 100.0, 2)

    diff_saved_path = None
    if output_diff_path:
        dest_diff = Path(output_diff_path)
        dest_diff.parent.mkdir(parents=True, exist_ok=True)
        # Highlight differences
        enhanced_diff = ImageOps.invert(diff)
        enhanced_diff.save(dest_diff)
        diff_saved_path = str(dest_diff.resolve())

    composite_saved_path = None
    if output_composite_path:
        dest_comp = Path(output_composite_path)
        dest_comp.parent.mkdir(parents=True, exist_ok=True)

        # Scale down for side-by-side if too large
        max_h = 600
        scale = min(1.0, max_h / ref_size[1])
        thumb_w = int(ref_size[0] * scale)
        thumb_h = int(ref_size[1] * scale)

        c_ref = ref_img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        c_ren = ren_img_aligned.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        c_diff = diff.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)

        header_height = 40
        composite = Image.new("RGB", (thumb_w * 3 + 40, thumb_h + header_height + 20), (245, 247, 250))
        draw = ImageDraw.Draw(composite)

        # Draw labels
        draw.text((20, 12), "REFERENCE", fill=(55, 65, 81))
        draw.text((thumb_w + 30, 12), "RENDERED (IMPLEMENTATION)", fill=(55, 65, 81))
        draw.text((thumb_w * 2 + 40, 12), f"DIFF ({diff_percentage}% mismatch)", fill=(220, 38, 38))

        composite.paste(c_ref, (10, header_height))
        composite.paste(c_ren, (thumb_w + 20, header_height))
        composite.paste(c_diff, (thumb_w * 2 + 30, header_height))

        composite.save(dest_comp)
        composite_saved_path = str(dest_comp.resolve())

    return ComparisonResult(
        similarity_score=round(similarity_score, 4),
        difference_percentage=diff_percentage,
        reference_size=ref_size,
        rendered_size=ren_size,
        aspect_ratio_mismatch=aspect_mismatch,
        composite_image_path=composite_saved_path,
        diff_image_path=diff_saved_path,
        is_acceptable=similarity_score >= acceptable_threshold,
    )


def generate_discrepancy_checklist() -> str:
    """Returns the visual inspection checklist to guide the refinement pass."""
    return """### Visual Inspection Checklist
1. **Overall Composition**: Does the page layout flow match the reference in order and positioning?
2. **Typography**: Are font weights, headings, body text sizes, and letter spacing matching?
3. **Color Palette**: Are background tints, brand primary/secondary colors, and text contrast accurate?
4. **Spacing & Alignment**: Are margins, padding, flexbox gaps, and container widths aligned?
5. **Assets & Media**: Do logos, icons, avatars, and hero graphics appear with correct dimensions?
6. **Borders & Shadows**: Are card rounded corners (`rounded-lg`, `rounded-2xl`) and drop shadows faithful?
7. **Mobile Responsiveness**: Does the layout gracefully wrap without horizontal overflow on small screens?
"""
