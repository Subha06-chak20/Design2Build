# Design2Build

> **Agent-Native Visual Engineering Skills & Workflows for Antigravity, LLM Coding Agents, and Developers.**

**Design2Build** is an open-source collection of reusable AI agent skills, core engines, and CLI workflows that turn visual specifications—screenshots, UI mockups, and web designs—into production-grade, pixel-accurate, and truly responsive frontend code.

---

## 📖 Table of Contents

- [Overview](#overview)
- [Skills Catalog](#skills-catalog)
  - [1. screenshot-to-code](#1-screenshot-to-code)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Install the Core Engine & CLI](#2-install-the-core-engine--cli)
  - [3. Install Browser Engine (Playwright)](#3-install-browser-engine-playwright)
- [How to Use as an Antigravity Skill](#how-to-use-as-an-antigravity-skill)
  - [Option A: Workspace-Local Installation](#option-a-workspace-local-installation)
  - [Option B: Global User Installation](#option-b-global-user-installation)
- [CLI Quick Reference (`stc`)](#cli-quick-reference-stc)
- [Supported Frontend Stacks](#supported-frontend-stacks)
- [Responsive Layout Architecture](#responsive-layout-architecture)
- [Repository Structure](#repository-structure)
- [Contributing](#contributing)
- [License](#license)

---

## 🔍 Overview

When modern AI agents generate frontends from screenshot images, they frequently suffer from two critical pitfalls:
1. **Narrow Viewport Trapping**: Hardcoding reference screenshot dimensions (e.g. `w-[736px]`, `min-w-[736px]`, `absolute left-[35px] top-[45px]`), causing websites to appear as a narrow centered strip on desktop monitors.
2. **Lack of Visual Verification**: Writing code without validating how the rendered page actually looks across different viewports or whether elements cause horizontal scrollbars on mobile.

**Design2Build** solves this by providing:
- **Responsive Layout Hierarchy Guidelines**: Guarantees fluid layouts (`w-full` $\to$ `px-4 sm:px-6 lg:px-8` $\to$ `max-w-7xl mx-auto` $\to$ CSS Grid / Flexbox).
- **Headless Browser Verification**: Automatically renders generated pages in headless Chromium / Edge across 4 standardized viewports (Mobile 375px, Tablet 768px, Desktop 1024px, Large Desktop 1440px).
- **Responsive Health Audits**: Automatically detects horizontal overflow, identifies offending DOM elements, and warns against artificially narrow desktop containers.
- **Outward-Rounding Asset Cropper**: Crops logos, badges, and icons from the reference image without boundary pixel clipping.
- **Harness Independence**: Designed natively for Google Antigravity, but easily pluggable into standalone CLI scripts, Claude Code, or Codex.

---

## 🧰 Skills Catalog

### 1. `screenshot-to-code`
- **Location**: [`skills/screenshot-to-code/`](skills/screenshot-to-code/)
- **Trigger Phrasing**: *"convert this screenshot to code"*, *"build this website from reference"*, *"recreate this UI"*, or uploading a UI image to Antigravity.
- **Capabilities**:
  - **Stage 1 — Ingestion & Viewport Detection**: Analyzes layout hierarchy, color palette, fonts, and aspect ratio.
  - **Stage 2 — Asset Extraction**: Normalizes bounding boxes and crops assets using generous pixel geometry.
  - **Stage 3 — Scaffold**: Initializes workspace with CDN boilerplates (Tailwind, React 18, Vue 3, Ionic, Bootstrap).
  - **Stage 4 — Responsive Implementation**: Employs responsive container patterns forbidding hardcoded screenshot widths.
  - **Stage 5 — Multi-Viewport Browser Render**: Captures screenshots across mobile, tablet, and desktop viewports.
  - **Stage 6 — Responsive Health Audit**: Checks for `scrollWidth > innerWidth` overflow and runtime console errors.
  - **Stage 7 — Perceptual Visual Verification**: Generates side-by-side composites and diff heatmaps.
  - **Stage 8 — Iterative Refinement**: Applies surgical corrections directly to discrepant DOM elements.

---

## ⚙️ Prerequisites

- **Python**: Version 3.10 or higher
- **Node.js**: (Optional, only needed if using npm-based build workflows)
- **Git**: Installed and configured
- **Operating System**: Windows, macOS, or Linux

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Subha06-chak20/Design2Build.git
cd Design2Build
```

### 2. Install the Core Engine & CLI
Install the core Python package in editable mode:
```bash
pip install -e ./skills/screenshot-to-code/core
```

Verify the installation:
```bash
stc doctor
```

### 3. Install Browser Engine (Playwright)
To enable headless browser rendering and responsive visual audits:
```bash
playwright install chromium
```
*(On Windows systems, `stc` will also automatically detect and use system Microsoft Edge if Chromium is not yet installed).*

---

## 🤖 How to Use as an Antigravity Skill

Antigravity automatically discovers skills defined with a `SKILL.md` file.

### Option A: Workspace-Local Installation
To use the skill inside your current project workspace, copy or symlink the skill folder into `.agents/skills/`:

```bash
# Inside your project repository:
mkdir -p .agents/skills
cp -r /path/to/Design2Build/skills/screenshot-to-code .agents/skills/
```

### Option B: Global User Installation
To make the skill accessible across all your Antigravity sessions on your machine:

**Windows**:
```powershell
Copy-Item -Recurse "skills/screenshot-to-code" "$env:USERPROFILE\.gemini\antigravity\skills\"
```

**macOS / Linux**:
```bash
cp -r skills/screenshot-to-code ~/.gemini/antigravity/skills/
```

Once installed, simply send your screenshot to Antigravity and prompt:
> *"Recreate this UI in HTML and Tailwind CSS. Ensure it is fully responsive and verified across viewports."*

---

## 💻 CLI Quick Reference (`stc`)

The package includes a fast standalone CLI (`stc`) to test, preview, and audit your code:

| Command | Description |
| :--- | :--- |
| `stc doctor` | Check environment, dependencies, and headless browser status |
| `stc status` | Display package version, viewports, and supported stacks |
| `stc preview index.html --viewport all` | Render and capture screenshots across all 4 responsive viewports |
| `stc preview index.html --viewport mobile` | Render mobile viewport (375x812px) |
| `stc check reference.png --responsive` | Run visual diff comparison and multi-viewport responsive health audit |
| `stc crop reference.png --coords [ymin,xmin,ymax,xmax] --out ./assets/logo.png` | Crop asset with outward-rounding geometry |

### Example Responsive Health Audit Output
```text
=== Screenshot-to-Code Visual Verification ===
Target Viewport      : desktop_wide (1280x832px)

--- Responsive Layout Health Audit ---
  ✓ Mobile (375x812px): Healthy & fluid (Container width: 375px)
  ✓ Tablet (768x1024px): Healthy & fluid (Container width: 768px)
  ✓ Desktop (1024x768px): Healthy & fluid (Container width: 1024px)
  ✓ Large_Desktop (1440x900px): Healthy & fluid (Container width: 1440px)

[✓] All responsive viewports verified: Fluid, no horizontal overflow, zero runtime errors.
```

---

## 🧱 Supported Frontend Stacks

- **`html_tailwind`** (Default): Standalone HTML5 + Tailwind CSS CDN + Font Awesome 6 + Google Fonts.
- **`react_tailwind`**: React 18 UMD + Babel Standalone 7.25.6 + Tailwind CSS.
- **`vue_tailwind`**: Vue 3 Global CDN + Tailwind CSS.
- **`bootstrap`**: Standard Bootstrap 5.3.2 + Bootstrap Icons.
- **`ionic_tailwind`**: Ionic 5+ Mobile Web Component CDN + Tailwind CSS.

---

## 📐 Responsive Layout Architecture

Every design implemented through Design2Build follows this strict container hierarchy:

```text
FULL VIEWPORT CANVAS (w-full min-h-screen bg-...)
     ↓
RESPONSIVE PAGE GUTTER (px-4 sm:px-6 lg:px-8)
     ↓
MAX-WIDTH CONTENT BOUNDARY (max-w-7xl mx-auto)
     ↓
SECTIONS (w-full py-8 sm:py-12 lg:py-16)
     ↓
RESPONSIVE REFLOW GRIDS (grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5)
```

**Key Directives**:
- **Never Hardcode Screenshot Dimensions**: Reference image resolution is a visual spec, never a fixed CSS width constraint.
- **Zero Coordinate Layouts**: `position: absolute` is prohibited for major layout blocks; CSS Grid and Flexbox are used exclusively.
- **Zero Horizontal Overflow**: All flex items use `min-w-0` to avoid flex shrinkage blowouts on compact viewports.

---

## 📂 Repository Structure

```
Design2Build/
├── .gitignore
├── LICENSE                          # MIT License
├── README.md                        # Documentation
└── skills/
    └── screenshot-to-code/          # Primary Visual Coding Skill
        ├── SKILL.md                 # Antigravity skill specification & runbook
        ├── references/
        │   ├── stacks.md            # CDN boilerplates & stack definitions
        │   └── verification_checklist.md
        ├── scripts/
        │   ├── crop_asset.py        # Standalone asset cropping script
        │   ├── diff_preview.py      # Perceptual difference calculator
        │   └── render_preview.py    # Headless browser preview renderer
        └── core/                    # Core Python engine & CLI
            ├── README.md
            ├── pyproject.toml       # Package configuration
            ├── requirements.txt
            ├── stc_core/            # Core library modules
            │   ├── adapters/        # Harness adapters (Antigravity, Standalone, etc.)
            │   ├── assets/          # Asset extraction & detection
            │   ├── preview/         # Playwright multi-viewport rendering
            │   ├── prompts/         # Responsive recipes & prompt engineering
            │   ├── verification/    # Perceptual diff & comparator
            │   ├── cli.py           # Click CLI implementation
            │   └── workflow.py      # 8-stage orchestrator
            └── tests/
                └── test_core.py     # 11 automated unit & integration tests
```

---

## 🧪 Testing

Run the full pytest suite to verify all core components, asset extractors, prompt directives, and responsive diagnostics:

```bash
pytest skills/screenshot-to-code/core/tests/test_core.py -v
```

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request if you want to propose a new skill, add an adapter for another agent harness, or enhance visual comparison heuristics.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
