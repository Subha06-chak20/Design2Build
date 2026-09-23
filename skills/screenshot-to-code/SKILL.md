---
name: screenshot-to-code
description: >-
  Converts screenshots, UI mockups, or web designs into working, pixel-accurate,
  visually-verified code projects. Uses headless browser rendering, screenshot capture,
  asset extraction, and multi-pass visual refinement to match the reference design.
  Trigger when the user asks to "build this website from a screenshot", "convert screenshot to code",
  "recreate this UI", or gives an image to implement.
---

# Screenshot-to-Code: Antigravity Visual Coding Workflow

This skill guides Antigravity through the complete 8-stage Screenshot-to-Code visual reconstruction pipeline.
Rather than generating rough one-shot approximations, this workflow:
1. Ingests reference visual mockups (via `@reference/...`, chat attachment, or CLI).
2. Extracts real visual assets (logos, icons, photos) directly into `./assets/`.
3. Scaffolds a project (or integrates into existing Next.js, Vite, React, or HTML stacks).
4. Generates initial code with battle-tested stack boilerplates.
5. Renders the implementation in a real headless browser (Chromium / Edge fallback).
6. Runs automated visual comparison and produces diff / composite artifacts.
7. Iteratively refines the code to resolve layout, typography, color, and spacing discrepancies.
8. Delivers a self-contained, working project.

---

## 3 Unified Input Methods

All input methods converge on the exact same 8-stage visual coding pipeline:

### Method A: In-Project Reference (Preferred)
The user places the image inside the workspace:
```text
my-project/
└── reference/
    └── homepage.png
```
User prompt:
```text
@reference/homepage.png
Use Screenshot-to-Code.
Recreate this as a working website in the current project.
```

### Method B: Chat Attachment
The user attaches or drags an image into chat:
```text
[Attached Image: dashboard.png]
Use Screenshot-to-Code.
Recreate this UI as a React + Tailwind component.
```
*Antigravity saves the attached image to `./reference/reference.png` and begins the pipeline.*

### Method C: Command-Line Interface (`stc`)
For headless automation or scripting from terminal/PowerShell:
```bash
stc generate ./reference/homepage.png --out ./my-project --stack html_tailwind
```

---

## Core Principle: Responsive Architecture vs. Reference Dimensions

> [!IMPORTANT]
> **The screenshot is a visual reference for DESIGN, NOT a command to hardcode its physical pixel dimensions.**
> - **NEVER HARDCODE SCREENSHOT WIDTH**: If a screenshot is 736px or 576px wide, do NOT generate `w-[736px]`, `min-w-[736px]`, or `width: 736px`.
> - **NEVER USE ABSOLUTE POSITIONING FOR LAYOUT**: Content blocks (hero, grids, cards, banners, footers) must use normal document flow, Flexbox (`flex flex-col md:flex-row`), and CSS Grid (`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5`).
> - **CONTAINER HIERARCHY**:
>   ```text
>   FULL VIEWPORT (w-full min-h-screen bg-...)
>        ↓
>   RESPONSIVE PAGE PADDING (px-4 sm:px-6 lg:px-8)
>        ↓
>   MAX-WIDTH CONTENT CONTAINER (max-w-7xl mx-auto)
>        ↓
>   SECTION (w-full my-8 md:my-16)
>        ↓
>   RESPONSIVE COMPONENTS (Grid / Flex with breakpoint modifiers)
>   ```
> - **MULTI-VIEWPORT TESTING**: Every project must be tested and verified across:
>   - Mobile (375 x 812)
>   - Tablet (768 x 1024)
>   - Desktop (1024 x 768)
>   - Wide Desktop (1440 x 900)

---

## Workspace Modes: Empty Directory vs. Existing Project

### Mode 1: Empty Directory (New Project Scaffolding)
- Prompt user if stack is ambiguous: "What stack should I build this in? 1. Plain HTML/CSS/JS (Live Server compatible), 2. React, 3. Existing project/framework".
- If Plain HTML/CSS/JS: Initialize project with `index.html`, `style.css`, `script.js`, and `./assets/`.
- If Tailwind CDN: `index.html`, `./assets/`, `README.md`.
- No Python backend server is created or required! Open directly with VS Code Live Server ("Go Live") or double-click `index.html`.

### Mode 2: Existing Project Integration (Non-Destructive)
- **Inspect first**: Check `package.json`, framework (Next.js, Vite, Nuxt, Remix), routing structure (`src/pages`, `app/`, `src/components/`), and styling setup (Tailwind CSS, CSS modules, Styled Components).
- **Preserve configuration**: DO NOT clobber `package.json`, configuration files, or existing routes.
- **Generate component or page**: Place new code into the appropriate project path (e.g. `src/components/HeroSection.tsx` or `src/pages/Landing.tsx`).
- **Assets**: Save extracted visual assets into the project's static folder (e.g. `public/assets/` or `src/assets/`).
- **Render & Verify**: Render the local dev server or static export in headless browser to verify parity.

---

## Multiple Reference Images

When multiple reference images are provided:
1. **Desktop vs. Mobile Viewports**:
   - E.g., `reference/desktop.png` and `reference/mobile.png`.
   - Implement responsive Tailwind breakpoints (`md:`, `lg:`).
   - Render both viewports (Desktop: `1280x832` / `1440x900`, Mobile: `375x812`) and verify against both references.
2. **Multiple Pages / Tabs**:
   - E.g., `reference/overview.png` and `reference/analytics.png`.
   - Scaffold tabbed navigation or multi-page routing.
   - Extract shared assets into `./assets/` and verify each view.
3. **Dark Mode / Light Mode**:
   - E.g., `reference/light.png` and `reference/dark.png`.
   - Implement `class="dark"` toggle with Tailwind `dark:` classes.

---

## Agent Output Formatting

During execution, keep user communication clean, focused, and progress-driven. Emit the structured status checklist:

```text
Screenshot-to-Code
✓ Reference loaded: reference/homepage.png
✓ Screenshot analyzed: layout hierarchy, colors, typography, fluid grid structure
✓ Assets identified & extracted to ./assets/
✓ Project initialized: html_tailwind (responsive container hierarchy)
✓ Initial implementation created (Grid reflow + Flexbox, no absolute layout)
✓ Headless browser started (Playwright Chromium)
✓ Responsive audit: Mobile (375px), Tablet (768px), Desktop (1024px), Wide Desktop (1440px)
✓ Reference comparison completed (Initial similarity: XX%)
↻ Refining layout & spacing
↻ Refining typography & colors
✓ Final browser verification (Final similarity: YY%, 0 overflow, fluid expansion)
✓ Project ready: Open with VS Code Live Server
```

---

## The 8-Stage Procedure

### Stage 1: Analyze Reference Screenshot
Examine visual structure:
- **Layout Hierarchy**: Header/navbar, hero section, content grids/cards, sidebars, footer.
- **Fluid Proportions**: Infer how elements scale outside the observed viewport. Distinguish fixed elements (icons, logos, badges) from fluid elements (containers, heroes, card grids).
- **Typography**: Display vs body fonts, weights (400, 600, 700), responsive font sizes (`text-2xl sm:text-3xl lg:text-5xl`), text colors.
- **Color Palette**: Exact background tones (`bg-slate-50`, `#0f172a`), card surfaces (`bg-white`), accent colors (`#3b82f6`, `#10b981`), borders (`border-slate-200`).
- **Spacing & Alignment**: Centered container max-widths (`max-w-7xl mx-auto`), responsive page paddings (`px-4 sm:px-6 lg:px-8`), flex/grid gaps (`gap-4 md:gap-8`).

### Stage 2: Identify and Extract Visual Assets
Do not leave logos or hero graphics as empty placeholders.
1. Estimate normalized 0-1000 bounding boxes: `[ymin, xmin, ymax, xmax]`.
2. Crop and save using `stc`:
   ```bash
   stc extract-assets <reference_path> --box "ymin,xmin,ymax,xmax" --name "logo" --out-dir "<project_dir>/assets"
   ```
   Or batch extract:
   ```bash
   stc extract-assets <reference_path> --boxes-file assets.json --out-dir "<project_dir>/assets"
   ```
3. Extracted assets are placed in `./assets/` and referenced in HTML as `<img src="./assets/logo.png">`. Use `object-cover` or `object-contain`.

### Stage 3: Choose Implementation Stack & Boilerplate
Select the appropriate recipe from [Stack Boilerplates](./references/stacks.md).
Default to `html_tailwind` (or modular `html_css` if Plain HTML/CSS/JS is requested).

### Stage 4: Scaffolding and Code Generation
1. Write the code into the project (`<project_dir>/index.html` or target component).
2. Adhere to core replication guidelines:
   - Use the exact copy and text visible in the reference.
   - Use Font Awesome 5 (`<i class="fas fa-..."></i>`) or inline SVGs for UI icons.
   - Use Google Fonts via `<link href="https://fonts.googleapis.com/css2?..." rel="stylesheet">`.
   - Ensure interactive states (`hover:`, `focus:`, button clicks) are functional.
   - **Enforce Responsive Architecture**:
     - Wrap page in `w-full min-h-screen`.
     - Center content inside `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`.
     - Hero: 2 columns on desktop (`grid-cols-1 lg:grid-cols-12` or `lg:flex-row`), 1 column on mobile.
     - Grids: Responsive breakpoints (`grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5`).
     - Zero horizontal overflow (`overflow-x-hidden` on body).

### Stage 5: Render Across Responsive Viewports
Capture pixel-accurate browser screenshots across all standard viewports:
```bash
stc preview "<project_dir>/index.html" --out "<project_dir>/preview.png" --viewport all
```
Or check individual viewports:
```bash
stc preview "<project_dir>/index.html" --out "<project_dir>/preview_mobile.png" --viewport mobile
stc preview "<project_dir>/index.html" --out "<project_dir>/preview_tablet.png" --viewport tablet
stc preview "<project_dir>/index.html" --out "<project_dir>/preview_desktop.png" --viewport desktop
stc preview "<project_dir>/index.html" --out "<project_dir>/preview_wide.png" --viewport large_desktop
```
The renderer uses Playwright Chromium (or system Edge fallback), awaits `networkidle`, verifies `document.fonts.ready`, audits horizontal overflow, and captures full-resolution PNGs.

### Stage 6: Visual & Responsive Verification
Compare the rendered browser capture against the reference screenshot and run responsive checks:
```bash
stc check <reference_path> --project "<project_dir>" --responsive
```
Inspect the comparison metrics and checklist:
- Similarity Score (evaluated against matching reference aspect ratio).
- Responsive Health Audit:
  - [✓] Mobile (375x812): No horizontal overflow (`scrollWidth <= innerWidth`)
  - [✓] Tablet (768x1024): Clean grid reflow
  - [✓] Desktop (1024x768): Full content expansion
  - [✓] Wide Desktop (1440x900): Content container expands gracefully (no narrow centered strip)
  - [✓] Zero runtime JavaScript errors or broken assets

### Stage 7: Iterative Refinement
1. Identify specific discrepancies from the diff composite and responsive diagnostics.
2. If desktop is too narrow, remove fixed width values (`w-[...]`) and apply `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`.
3. If cards overflow on mobile, adjust grid breakpoints (`grid-cols-1 sm:grid-cols-2`).
4. Apply targeted edits directly to `<project_dir>/index.html` (or component file).
5. Re-render preview and verify score improvement.
6. Continue refining until the design closely matches the reference ($\ge 90\%$ similarity) and passes all responsive checks.

### Stage 8: Deliver Final Working Project
Ensure the project is completely runnable without any backend servers:
- Project files: `index.html` (or `index.html` + `style.css` + `script.js`), `assets/`, `README.md`.
- No broken asset links (404s) or missing fonts.
- Provide user instructions to test locally:
  - **VS Code Live Server**: Right-click `index.html` $\to$ **Open with Live Server**.
  - **Direct Browser**: Double-click `index.html` or open `file:///.../index.html`.
  - **Node Static Server (Optional)**: `npx serve .`
