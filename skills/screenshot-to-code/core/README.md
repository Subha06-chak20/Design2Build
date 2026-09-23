# Screenshot-to-Code Core (`stc-core`)

A modular, agent-native visual coding engine extracted from [abi/screenshot-to-code](https://github.com/abi/screenshot-to-code).

## Capabilities
- **Multi-Stack Recipes**: Preserved CDN templates for Tailwind CSS, React 18 + Babel Standalone 7.25.6, Vue 3, Bootstrap 5.3, Ionic, and plain HTML/CSS.
- **Asset Extraction Engine**: Normalized bounding box detection and outward-rounding Pillow cropping to extract logos, photos, and icons directly from screenshots into local assets.
- **Headless Browser Preview**: Renders projects in Playwright Chromium and Windows Edge headless viewports (Desktop: 1280x832, Mobile: 342x684) with `networkidle` and font settling.
- **Visual Verification & Comparator**: Calculates perceptual similarity scores, difference percentages, and side-by-side comparison composites.
- **Harness Adapters**: Pluggable adapter architecture supporting Antigravity, Standalone APIs, Codex, and Claude Code.
- **CLI (`stc`)**: 8-stage progress reporting CLI for automated generation and testing.

## Installation
```bash
cd screenshot-to-code-core
pip install -e .
playwright install chromium
```

## CLI Usage
```bash
# Full workflow
python cli.py generate ./reference.png --stack html_tailwind --out ./output

# Browser preview
python cli.py preview ./output/index.html --out ./preview.png --viewport desktop

# Crop asset
python cli.py extract-assets ./reference.png --box "10,20,80,150" --name "logo" --out-dir ./output/assets

# Visual diff
python cli.py diff ./reference.png ./preview.png --composite-out ./composite.png
```
