# Design2Build Core Engine (`design2build` / `d2b`)

A modular, agent-native visual coding engine and CLI workflow designed for Antigravity, LLM agents, and developers.

## Capabilities
- **Multi-Stack Recipes**: Preserved CDN templates for Tailwind CSS, React 18 + Babel Standalone 7.25.6, Vue 3, Bootstrap 5.3, Ionic, and plain HTML/CSS.
- **Asset Extraction Engine**: Normalized bounding box detection and outward-rounding Pillow cropping to extract logos, photos, and icons directly from screenshots into local assets.
- **Headless Browser Preview**: Renders projects in Playwright Chromium and Windows Edge headless viewports across 5 standardized viewports (Mobile: 375x812, Tablet: 768x1024, Desktop: 1024x768, Desktop Wide: 1280x832, Large Desktop: 1440x900) with `networkidle` and font settling.
- **Responsive Health Audits**: In-page DOM inspection detecting horizontal overflow (`scrollWidth > innerWidth`), identifying offending DOM elements, and checking for artificially narrow desktop containers.
- **Visual Verification & Comparator**: Calculates perceptual similarity scores, difference percentages, and side-by-side comparison composites.
- **Harness Adapters**: Pluggable adapter architecture supporting Antigravity, Standalone APIs, Codex, and Claude Code.
- **CLI (`d2b` / `design2build` / `stc`)**: Multi-command CLI for automated generation, previewing, and responsive verification.

## Installation
```bash
pip install -e .
playwright install chromium
```

## CLI Usage
```bash
# Doctor / Health Check
d2b doctor

# Multi-viewport responsive preview
d2b preview ./index.html --viewport all

# Visual diff & responsive audit against reference
d2b check ./reference.png --responsive

# Outward-rounding asset crop
d2b crop ./reference.png --coords [ymin,xmin,ymax,xmax] --out ./assets/logo.png
```
