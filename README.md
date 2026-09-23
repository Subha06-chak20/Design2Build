# Design2Build

> **Agent-Native Visual Engineering Skills & Workflows for Antigravity, Claude Code, and AI Coding Agents.**

**Design2Build** is an open-source collection of reusable AI agent skills, core engines, and CLI workflows that turn visual specifications—screenshots, UI mockups, and web designs—into production-grade, pixel-accurate, and truly responsive frontend code.

---

## 📖 Table of Contents

- [Overview](#overview)
- [Skills Catalog](#skills-catalog)
  - [1. design2build](#1-design2build)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Install the Core Engine & CLI](#2-install-the-core-engine--cli)
  - [3. Install Browser Engine (Playwright)](#3-install-browser-engine-playwright)
- [How to Use as an AI Coding Skill](#how-to-use-as-an-ai-coding-skill)
  - [Workspace Installation](#workspace-installation)
  - [Global Installation](#global-installation)
  - [Copy-Paste Prompt for AI Agents](#copy-paste-prompt-for-ai-agents)
- [CLI Quick Reference (`d2b`)](#cli-quick-reference-d2b)
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
- **Agent Independence**: Works natively with any vision-capable AI coding assistant (such as Antigravity, Claude Code by Anthropic, Cursor, Codex, or Windsurf) or via standalone CLI scripts.

---

## 🧰 Skills Catalog

### 1. `design2build`
- **Location**: [`skills/design2build/`](skills/design2build/)
- **Skill Name**: `design2build`
- **Trigger Phrasing**: *"use Design2Build"*, *"convert this screenshot to code"*, *"build this website from reference"*, *"recreate this UI"*, or uploading a UI mockup to your AI coding assistant.
- **Capabilities**:
  - **Stage 0 — Intelligent Project Setup**: Context-aware inference from user prompts, workspace files (`package.json`), and reference aspect ratios to determine stack, devices, and run mode without redundant questions.
  - **Stage 1 — Implementation Plan Confirmation**: Generates a structured milestone plan customized to the project and confirms alignment before generating code.
  - **Stage 2 — Ingestion & Viewport Detection**: Analyzes layout hierarchy, color palette, fonts, and aspect ratio.
  - **Stage 3 — Asset Extraction**: Normalizes bounding boxes and crops assets using generous pixel geometry into `./assets/`.
  - **Stage 4 — Stack Selection**: Configures CDN boilerplates (Tailwind, React 18, Vue 3, Ionic, Bootstrap).
  - **Stage 5 — Scaffolding & Responsive Implementation**: Generates code adhering to fluid container hierarchy patterns forbidding hardcoded screenshot widths.
  - **Stage 6 — Multi-Viewport Browser Render**: Captures screenshots across mobile, tablet, desktop, and wide desktop viewports.
  - **Stage 7 — Responsive Health Audit**: Checks for `scrollWidth > innerWidth` overflow and runtime console errors.
  - **Stage 8 — Perceptual Visual Verification**: Generates side-by-side composites and diff heatmaps against reference images.
  - **Stage 9 — Iterative Refinement & Packaging**: Applies surgical corrections directly to discrepant DOM elements and packages self-contained files.


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
pip install -e ./skills/design2build/core
```

Verify the installation (commands `d2b`, `design2build`, and `stc` are all available):
```bash
d2b doctor
```

### 3. Install Browser Engine (Playwright)
To enable headless browser rendering and responsive visual audits:
```bash
playwright install chromium
```
*(On Windows systems, `d2b` will also automatically detect and use system Microsoft Edge if Chromium is not yet installed).*

---

## 🤖 How to Use as an AI Coding Skill

Design2Build is compatible with any AI coding agent equipped with vision capabilities (such as Antigravity, Claude Code by Anthropic, Cursor, Codex, or Windsurf). AI coding assistants automatically discover skills defined with a `SKILL.md` file.

### Workspace Installation
To use Design2Build inside your project workspace, copy the skill folder into `.agents/skills/`:

```bash
mkdir -p .agents/skills
cp -r /path/to/Design2Build/skills/design2build .agents/skills/
```

### Global Installation
To make the skill accessible across all projects on your machine:

**Windows**:
```powershell
Copy-Item -Recurse "skills/design2build" "$env:USERPROFILE\.gemini\config\skills\"
```

**macOS / Linux**:
```bash
cp -r skills/design2build ~/.gemini/config/skills/
```

---

### Copy-Paste Prompt for AI Agents

When moving to another computer, new device, or workspace, paste this prompt directly into your AI coding assistant (Antigravity, Claude Code, Cursor, etc.):

```text
Please setup and use the Design2Build skill from https://github.com/Subha06-chak20/Design2Build.git:

1. Clone the repository and install the core tools:
   git clone https://github.com/Subha06-chak20/Design2Build.git
   pip install -e ./Design2Build/skills/design2build/core

2. Install the skill:
   mkdir -p .agents/skills
   cp -r ./Design2Build/skills/design2build .agents/skills/

3. Read .agents/skills/design2build/SKILL.md to load the 10-stage runbook.

4. Recreate my reference design [ATTACH_IMAGE_OR_PATH] using the Design2Build workflow:
   - Stage 0: Run `d2b setup` to infer the stack, target devices, and run mode without asking unnecessary questions.
   - Stage 1: Present the implementation plan for my confirmation.
   - Stage 2–9: Extract visual assets to ./assets/, implement fluid responsive layout (no fixed screenshot widths), verify across viewports with `d2b check --responsive`, and refine until visually matching!
```

---

## 💻 CLI Quick Reference (`d2b`)

The package includes a fast standalone CLI (`d2b`, aliased also as `design2build` and `stc`) to test, preview, audit, and scaffold your code:

| Command | Description |
| :--- | :--- |
| `d2b setup [REF] [--prompt "..."]` | Run intelligent project setup (infers stack, devices, run mode, and generates plan) |
| `d2b setup --mode advanced` | Launch full interactive setup wizard for fine-grained configuration |
| `d2b generate <REF> [--config CFG]` | Run end-to-end visual coding workflow with project target configuration |
| `d2b generate <REF> --interactive` | Launch setup wizard then immediately generate code |
| `d2b doctor` | Check environment, dependencies, and headless browser status |
| `d2b status` | Display package version, viewports, and detected `d2b.config.json` status |
| `d2b preview index.html --viewport all` | Render and capture screenshots across all 4 responsive viewports |
| `d2b preview index.html --viewport mobile` | Render mobile viewport (375x812px) |
| `d2b check reference.png --responsive` | Run visual diff comparison and multi-viewport responsive health audit |
| `d2b extract-assets <REF> --box "..."` | Crop asset with outward-rounding pixel geometry |

### Example Intelligent Setup Output (`d2b setup`)
```text
=== Design2Build Intelligent Project Setup ===
Workspace: /path/to/my-project
Prompt   : "Build an isolated pricing card component in React with Tailwind for mobile and desktop"

----------------------------------------
## DESIGN2BUILD PROJECT CONFIGURATION 

Project Type:
  Component

Technology / Stack:
  react_tailwind

Target Devices:
  Mobile + Desktop

Responsive Mode:
  Adaptive Breakpoints

Reference Intent:
  Isolated Component Reference

Project State:
  New Project

Run Mode:
  Vite Development Server

Backend:
  None (Frontend Only — Zero Python/FastAPI Server Required)
----------------------------------------

Configuration saved to: ./d2b.config.json
Implementation plan saved to: ./d2b.plan.md
```

### Example Responsive Health Audit Output
```text
=== Design2Build Visual Verification ===
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
- **`react_tailwind`**: React 18 UMD + Babel Standalone 7.25.6 + Tailwind CSS (Vite / Live Server compatible).
- **`vue_tailwind`**: Vue 3 Global CDN + Tailwind CSS.
- **`bootstrap`**: Standard Bootstrap 5.3.2 + Bootstrap Icons.
- **`ionic_tailwind`**: Ionic 5+ Mobile Web Component CDN + Tailwind CSS.
- **`html_css`**: Pure semantic HTML5 + responsive vanilla CSS.

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
├── .agents/
│   └── skills/
│       └── design2build/            # Pre-configured skill directory for agents
├── .gitignore
├── LICENSE                          # MIT License
├── README.md                        # Documentation
└── skills/
    └── design2build/                # Primary Visual Coding Skill
        ├── SKILL.md                 # Visual coding skill specification & 10-stage runbook
        ├── references/
        │   ├── stacks.md            # CDN boilerplates & stack definitions
        │   └── verification_checklist.md
        ├── scripts/
        │   ├── crop_asset.py        # Standalone asset cropping script
        │   ├── diff_preview.py      # Perceptual difference calculator
        │   └── render_preview.py    # Headless browser preview renderer
        └── core/                    # Core Python engine & CLI
            ├── README.md
            ├── pyproject.toml       # Package configuration (d2b v1.1.0)
            ├── requirements.txt
            ├── stc_core/            # Core library modules
            │   ├── adapters/        # Harness adapters (CLI, Antigravity, Claude Code, etc.)
            │   ├── assets/          # Asset extraction & detection
            │   ├── preview/         # Playwright multi-viewport rendering
            │   ├── prompts/         # Responsive recipes & prompt engineering
            │   ├── verification/    # Perceptual diff & comparator
            │   ├── config.py        # ProjectConfig & target configuration models
            │   ├── setup.py         # Context inference & plan generator
            │   ├── cli.py           # Click CLI implementation (setup, generate, doctor, check)
            │   └── workflow.py      # Visual coding orchestrator with target config
            └── tests/
                └── test_core.py     # 17 automated unit & integration tests
```

---

## 🧪 Testing

Run the full pytest suite to verify all core components, inference rules, plan generation, asset extractors, prompt directives, and responsive diagnostics:

```bash
pytest skills/design2build/core/tests/test_core.py -v
```

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request if you want to propose a new skill, add an adapter for another agent harness, or enhance visual comparison heuristics.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
