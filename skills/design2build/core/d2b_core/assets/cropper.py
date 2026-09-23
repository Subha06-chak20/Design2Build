"""
Asset Extraction and Cropping Engine
===================================
Design2Build asset extraction architecture.
Performs EXIF normalization, normalized bounding box validation, and outward-rounding
crops to ensure pixel-perfect asset preservation.
"""

import base64
import io
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageOps
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Normalized [ymin, xmin, ymax, xmax] coordinates in 0-1000 range."""
    ymin: float = Field(ge=0.0, le=1000.0)
    xmin: float = Field(ge=0.0, le=1000.0)
    ymax: float = Field(ge=0.0, le=1000.0)
    xmax: float = Field(ge=0.0, le=1000.0)

    @classmethod
    def from_list(cls, coords: Sequence[float]) -> "BoundingBox":
        if len(coords) != 4:
            raise ValueError("BoundingBox requires exactly 4 coordinates [ymin, xmin, ymax, xmax]")
        ymin, ymax = sorted((float(coords[0]), float(coords[2])))
        xmin, xmax = sorted((float(coords[1]), float(coords[3])))
        return cls(
            ymin=max(0.0, min(1000.0, ymin)),
            xmin=max(0.0, min(1000.0, xmin)),
            ymax=max(0.0, min(1000.0, ymax)),
            xmax=max(0.0, min(1000.0, xmax)),
        )


class ExtractedAsset(BaseModel):
    name: str
    filename: str
    box: BoundingBox
    filepath: Optional[str] = None
    data_url: Optional[str] = None
    width: int = 0
    height: int = 0


def normalize_image(image: Image.Image) -> Image.Image:
    """Apply EXIF transpose and preserve alpha channel."""
    oriented = ImageOps.exif_transpose(image)
    has_alpha = "A" in oriented.getbands() or "transparency" in oriented.info
    normalized = oriented.convert("RGBA" if has_alpha else "RGB")
    normalized.load()
    return normalized


def load_normalized_image(image_input: Union[str, Path, bytes, Image.Image]) -> Image.Image:
    """Load image from path, data-URL, bytes, or Image instance, normalizing EXIF."""
    if isinstance(image_input, Image.Image):
        return normalize_image(image_input)
    
    if isinstance(image_input, (str, Path)):
        str_input = str(image_input)
        if str_input.startswith("data:image/") and "," in str_input:
            _, encoded = str_input.split(",", 1)
            raw_bytes = base64.b64decode(encoded)
            with Image.open(io.BytesIO(raw_bytes)) as img:
                return normalize_image(img)
        with Image.open(image_input) as img:
            return normalize_image(img)
            
    if isinstance(image_input, bytes):
        with Image.open(io.BytesIO(image_input)) as img:
            return normalize_image(img)
            
    raise ValueError(f"Unsupported image input type: {type(image_input)}")


def crop_bounding_box(
    image: Image.Image,
    box: BoundingBox,
) -> Optional[Image.Image]:
    """Crop bounding box with outward-rounding geometry to avoid cutting borders."""
    width, height = image.size
    
    # Outward rounding ensures every border and shadow pixel is preserved
    left = max(0, min(width, math.floor(box.xmin / 1000.0 * width)))
    top = max(0, min(height, math.floor(box.ymin / 1000.0 * height)))
    right = max(0, min(width, math.ceil(box.xmax / 1000.0 * width)))
    bottom = max(0, min(height, math.ceil(box.ymax / 1000.0 * height)))

    if right <= left or bottom <= top:
        return None

    cropped = image.crop((left, top, right, bottom))
    if cropped.width <= 0 or cropped.height <= 0:
        return None

    return cropped


def image_to_data_url(image: Image.Image, fmt: str = "PNG") -> str:
    """Convert PIL image to base64 data-URL."""
    output = io.BytesIO()
    image.save(output, format=fmt)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    mime = "image/png" if fmt.upper() == "PNG" else f"image/{fmt.lower()}"
    return f"data:{mime};base64,{encoded}"


def extract_and_save_asset(
    source_image: Union[str, Path, Image.Image],
    box: Union[BoundingBox, List[float], Tuple[float, ...]],
    output_path: Union[str, Path],
    name: str = "asset",
) -> Optional[ExtractedAsset]:
    """Extract a single asset from source image using bounding box and save to disk."""
    img = load_normalized_image(source_image)
    bbox = box if isinstance(box, BoundingBox) else BoundingBox.from_list(box)
    
    cropped = crop_bounding_box(img, bbox)
    if cropped is None:
        return None

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(dest, format="PNG")

    return ExtractedAsset(
        name=name,
        filename=dest.name,
        box=bbox,
        filepath=str(dest.resolve()),
        data_url=image_to_data_url(cropped),
        width=cropped.width,
        height=cropped.height,
    )


def extract_assets_batch(
    source_image: Union[str, Path, Image.Image],
    assets_config: List[Dict[str, Any]],
    output_dir: Union[str, Path],
) -> Dict[str, ExtractedAsset]:
    """
    Batch extract multiple assets from a single source image.
    Each item in assets_config should have:
    - name: str (identifier, e.g. 'logo', 'hero_image')
    - box: [ymin, xmin, ymax, xmax] (0-1000 scale)
    - filename: optional str (e.g. 'logo.png')
    """
    img = load_normalized_image(source_image)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, ExtractedAsset] = {}
    for idx, item in enumerate(assets_config):
        name = item.get("name", f"asset_{idx}")
        raw_box = item.get("box") or item.get("box_2d")
        if not raw_box or len(raw_box) != 4:
            continue
            
        filename = item.get("filename", f"{name}.png")
        if not filename.endswith(".png"):
            filename = f"{filename}.png"
            
        dest_path = out_dir / filename
        asset = extract_and_save_asset(img, raw_box, dest_path, name=name)
        if asset:
            results[name] = asset

    return results


class AssetDetection(BaseModel):
    request_id: str
    image_index: Optional[int] = 1
    box_2d: Optional[List[float]] = None
    label: Optional[str] = None


class AssetDetectionBatch(BaseModel):
    detections: List[AssetDetection]


async def detect_assets_with_gemini(
    source_image: Union[str, Path, Image.Image],
    asset_descriptions: List[str],
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> List[Dict[str, Any]]:
    """
    Automated bounding box detection using Gemini vision API (adapted from upstream asset_extraction.py).
    Returns list of {'name': desc, 'box': [ymin, xmin, ymax, xmax]}.
    """
    import os
    gemini_key = api_key or os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError("Gemini asset detection requires GEMINI_API_KEY")

    from google import genai
    from google.genai import types

    img = load_normalized_image(source_image)
    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format="PNG")
    img_bytes = img_bytes_io.getvalue()

    client = genai.Client(api_key=gemini_key)
    requests_json = [
        {"request_id": f"asset-{i+1:04d}", "description": desc}
        for i, desc in enumerate(asset_descriptions)
    ]

    prompt = f"""Locate each requested visual asset in the attached image.
REQUESTS:
{requests_json}
BOUNDING-BOX RULES:
- box_2d is [ymin, xmin, ymax, xmax] normalized to 0-1000.
- Return the smallest axis-aligned box containing the visible requested asset.
"""

    response = await client.aio.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            types.Part.from_text(text=prompt),
        ],
        config=types.GenerateContentConfig(
            system_instruction="You are a precise 2D object detector for screenshot asset extraction. Return valid JSON only.",
            response_mime_type="application/json",
            response_schema=AssetDetectionBatch,
        ),
    )

    detected_boxes: List[Dict[str, Any]] = []
    parsed = response.parsed
    if parsed and hasattr(parsed, "detections"):
        for i, det in enumerate(parsed.detections):
            if det.box_2d and len(det.box_2d) == 4:
                desc = asset_descriptions[i] if i < len(asset_descriptions) else f"asset_{i}"
                detected_boxes.append({
                    "name": desc.lower().replace(" ", "_")[:30],
                    "box": det.box_2d,
                    "label": det.label or desc,
                })

    return detected_boxes

