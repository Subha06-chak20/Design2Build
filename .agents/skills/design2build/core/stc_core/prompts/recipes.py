"""
Screenshot-to-Code Stack Recipes and Prompt Templates
=====================================================
Preserved and adapted from the abi/screenshot-to-code architecture.
Includes battle-tested CDN configurations, stack boilerplates, and replication rules.
"""

from typing import Dict, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from stc_core.config import ProjectConfig


StackType = Literal[
    "html_tailwind",
    "react_tailwind",
    "vue_tailwind",
    "bootstrap",
    "ionic_tailwind",
    "html_css",
]

# Pinned and verified CDN links
CDN_TAILWIND = '<script src="https://cdn.tailwindcss.com"></script>'
CDN_FONT_AWESOME = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css"></link>'
CDN_BOOTSTRAP = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN" crossorigin="anonymous">'

# Pinned Babel Standalone 7.25.6: prevents Babel 8 JSX transform breaking standalone in-browser runtime
CDN_BABEL_STANDALONE = '<script src="https://unpkg.com/@babel/standalone@7.25.6/babel.min.js"></script>'
CDN_REACT_18 = '<script src="https://cdn.jsdelivr.net/npm/react@18.0.0/umd/react.development.js"></script>'
CDN_REACT_DOM_18 = '<script src="https://cdn.jsdelivr.net/npm/react-dom@18.0.0/umd/react-dom.development.js"></script>'

CDN_VUE_3 = '<script src="https://registry.npmmirror.com/vue/3.3.11/files/dist/vue.global.js"></script>'

STACK_BOILERPLATES: Dict[StackType, str] = {
    "html_tailwind": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>App</title>
  {CDN_TAILWIND}
  {CDN_FONT_AWESOME}
</head>
<body class="bg-gray-50 text-gray-900">
  <!-- Content -->
</body>
</html>""",

    "react_tailwind": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>React App</title>
  {CDN_REACT_18}
  {CDN_REACT_DOM_18}
  {CDN_BABEL_STANDALONE}
  {CDN_TAILWIND}
  {CDN_FONT_AWESOME}
</head>
<body class="bg-gray-50 text-gray-900">
  <div id="root"></div>
  <script type="text/babel">
    function App() {{
      return (
        <div className="min-h-screen">
          {{/* Content */}}
        </div>
      );
    }}
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>""",

    "vue_tailwind": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vue App</title>
  {CDN_VUE_3}
  {CDN_TAILWIND}
  {CDN_FONT_AWESOME}
</head>
<body class="bg-gray-50 text-gray-900">
  <div id="app">
    <!-- Content -->
  </div>
  <script>
    const {{ createApp, ref }} = Vue;
    createApp({{
      setup() {{
        return {{}};
      }}
    }}).mount('#app');
  </script>
</body>
</html>""",

    "bootstrap": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bootstrap App</title>
  {CDN_BOOTSTRAP}
  {CDN_FONT_AWESOME}
</head>
<body class="bg-light">
  <!-- Content -->
</body>
</html>""",

    "ionic_tailwind": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ionic App</title>
  <script type="module" src="https://cdn.jsdelivr.net/npm/@ionic/core/dist/ionic/ionic.esm.js"></script>
  <script nomodule src="https://cdn.jsdelivr.net/npm/@ionic/core/dist/ionic/ionic.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@ionic/core/css/ionic.bundle.css" />
  {CDN_TAILWIND}
</head>
<body>
  <ion-app>
    <ion-content>
      <!-- Content -->
    </ion-content>
  </ion-app>
  <script type="module">
    import ionicons from 'https://cdn.jsdelivr.net/npm/ionicons/+esm';
  </script>
  <script nomodule src="https://cdn.jsdelivr.net/npm/ionicons/dist/esm/ionicons.min.js"></script>
  <link href="https://cdn.jsdelivr.net/npm/ionicons/dist/collection/components/icon/icon.min.css" rel="stylesheet">
</body>
</html>""",

    "html_css": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>App</title>
  {CDN_FONT_AWESOME}
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; background: #f9fafb; color: #111827; }}
  </style>
</head>
<body>
  <!-- Content -->
</body>
</html>"""
}


SYSTEM_PROMPT = """You are an expert visual front-end coding agent.
Your objective is to transform a visual specification (screenshot or mockup) into high-quality, pixel-accurate, truly responsive, working code.

# Core Principles

## 1. Visual Specification vs. Responsive Reality
- The reference screenshot is a visual specification of the DESIGN, NOT a command to hardcode its physical pixel dimensions!
- NEVER hardcode the screenshot's width or height as a fixed CSS dimension (e.g., NEVER write `width: 736px`, `w-[736px]`, `min-w-[736px]`, `h-[1308px]`).
- Do NOT create a narrow, centered strip on desktop screens. The website must naturally expand across the available viewport while maintaining elegant max-width content boundaries.

## 2. Responsive Container Hierarchy
Always structure pages with this container hierarchy:
```text
FULL VIEWPORT (w-full min-h-screen bg-...)
     ↓
RESPONSIVE PAGE PADDING (px-4 sm:px-6 md:px-8 lg:px-12)
     ↓
MAX-WIDTH CONTENT CONTAINER (max-w-7xl mx-auto or min(100% - 2*padding, 1280px))
     ↓
SECTION (w-full my-8 md:my-16)
     ↓
RESPONSIVE COMPONENTS (CSS Grid / Flexbox with breakpoint modifiers)
```

## 3. Layout Flow & No Absolute Positioning
- Major page layout structures (hero sections, value prop strips, category rows, product card grids, promo banners, testimonials, footers) MUST use normal document flow, Flexbox, or CSS Grid.
- NEVER use `position: absolute` for major content sections, headings, paragraph text, or grid layouts.
- Absolute positioning is strictly reserved for small decorative badges, floating action buttons, icon overlays, or modal dismiss buttons.

## 4. Responsive Grid & Card Reflow
- For repeated components (e-commerce products, feature cards, categories, reviews), do NOT hardcode a single fixed column count like `grid-cols-5` or fixed pixel widths.
- Use responsive breakpoint classes:
  - Mobile (<640px): 1 or 2 cards per row (`grid-cols-1 sm:grid-cols-2`)
  - Tablet (640px - 1024px): 2 to 3 cards per row (`md:grid-cols-3`)
  - Desktop (1024px - 1280px): 4 to 5 cards per row (`lg:grid-cols-4 xl:grid-cols-5`)
  - Or use auto-fit grids: `grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))`

## 5. Responsive Hero Sections
- On desktop: Use a 2-column split layout (`grid grid-cols-1 lg:grid-cols-12` or `flex flex-col lg:flex-row`) with text on the left and imagery on the right.
- On mobile: Stack naturally with text on top and imagery underneath.
- Never use fixed heights like `h-[290px]` that clip content on mobile or leave vast empty gaps on wide desktop. Use `min-h-[...]` and responsive padding.

## 6. Fluid Typography & Spacing
- Use responsive text scales: `text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold`.
- Ensure buttons, inputs, and touch targets maintain minimum accessible sizes on mobile (min 44px touch target).
- Never allow horizontal overflow (`scrollWidth > window.innerWidth`). Ensure all containers are bounded within `w-full max-w-...`.

## 7. Assets & Visual Details
- Utilize real extracted assets (saved locally in `./assets/`) whenever available. Never stretch images; use `object-cover` or `object-contain`.
- Use exact visible copy, font families (via Google Fonts), colors, corner radii, and shadow elevations from the reference design.
"""


def get_replication_instructions(
    stack: StackType = "html_tailwind",
    extracted_assets: Optional[Dict[str, str]] = None,
    additional_instructions: Optional[str] = None,
    config: Optional["ProjectConfig"] = None,
) -> str:
    """Generate replication instructions customized for stack, project configuration, and extracted assets."""
    effective_stack = config.stack if (config and config.stack) else stack

    config_directives = []
    if config:
        config_directives.append("## Target Project Configuration")
        config_directives.append(f"- **Project Type**: {config.project_type.value.replace('_', ' ').title()}")
        config_directives.append(f"- **Target Devices**: {config.target_devices.value.replace('_', ' ').title()}")
        config_directives.append(f"- **Responsive Strategy**: {config.responsive_mode.value.replace('_', ' ').title()}")
        config_directives.append(f"- **Reference Intent**: {config.reference_intent.value.replace('_', ' ').title()}")
        config_directives.append(f"- **Run Mode**: {config.run_mode.value.replace('_', ' ').title()}")

        if config.project_type.value == "component":
            config_directives.append(
                "\n### Scope: Isolated Component\n"
                "Focus ONLY on recreating the specific isolated component or widget shown in the reference "
                "(e.g., navigation bar, card, dialog, banner). Do NOT build an entire dummy website around it. "
                "Keep the code modular, self-contained, and easily embeddable."
            )
        elif config.project_type.value == "redesign":
            config_directives.append(
                "\n### Scope: Modern Redesign\n"
                "Use the reference as an architectural and content baseline, but modernize typography, spacing, "
                "contrast, and responsive flow to state-of-the-art web standards."
            )

        if config.reference_intent.value == "exact_clone":
            config_directives.append(
                "\n### Visual Parity Directive\n"
                "Aim for exact visual parity: identical colors, typography weights, iconography, borders, "
                "and padding, while ensuring the layout is flexible and responsive."
            )
        elif config.reference_intent.value == "design_inspiration":
            config_directives.append(
                "\n### Inspiration Directive\n"
                "Adopt the aesthetic style, color palette, and visual language of the reference, but structure "
                "clean semantic HTML and flexible CSS tailored to the requested feature set."
            )

        if config.target_devices.value == "mobile_only":
            config_directives.append(
                "\n### Viewport Target: Mobile-First / Mobile-Only\n"
                "Optimize specifically for mobile touchscreens (375px - 480px). Touch targets must be at least 44x44px. "
                "Ensure drawer navigation, stacked cards, and compact headers."
            )
        elif config.target_devices.value == "desktop_only":
            config_directives.append(
                "\n### Viewport Target: Desktop-Focused\n"
                "Designed primarily for desktop screens (1024px+). Maximize horizontal visual hierarchy."
            )

    config_section = "\n".join(config_directives) + "\n\n" if config_directives else ""

    asset_section = ""
    if extracted_assets:
        items = "\n".join(f"- {name}: `./assets/{filename}`" for name, filename in extracted_assets.items())
        asset_section = f"""
## Available Extracted Assets
The following visual assets were extracted directly from the reference screenshot:
{items}
Use these exact relative file paths in your <img> tags or CSS backgrounds. Preserve their natural aspect ratio using object-contain or object-cover.
"""

    custom_text = f"\n## Additional User Instructions\n{additional_instructions.strip()}" if additional_instructions else ""

    viewports_desc = ""
    if config:
        vp_lines = "\n".join(f"{i+1}. {name.replace('_', ' ').title()}" for i, name in enumerate(config.resolve_viewports()))
        viewports_desc = f"""
## Verification Protocol
Your implementation will be verified in headless browsers across the configured viewports:
{vp_lines}
Ensure the layout reflows seamlessly and never collapses into a narrow column on desktop!
"""
    else:
        viewports_desc = """
## Verification Protocol
Your implementation will be verified in headless browsers across 4 viewports:
1. Mobile (375 x 812)
2. Tablet (768 x 1024)
3. Desktop (1024 x 768)
4. Wide Desktop (1440 x 900)
Ensure the layout reflows seamlessly and never collapses into a narrow column on desktop!
"""

    return f"""Generate code for a web page that visually matches the provided reference design while implementing a fully responsive layout system.

Selected stack: {effective_stack}

{config_section}## CRITICAL: Responsive Architecture Requirements (Do NOT violate)
1. DO NOT HARDCODE SCREENSHOT DIMENSIONS: The screenshot represents ONE observed view of the design. Do NOT create a fixed-width container matching the screenshot's width (e.g. DO NOT write `w-[736px]`, `w-[576px]`, `width: 736px`).
2. FLUID CONTAINER SYSTEM: Wrap the page in `w-full min-h-screen`. Content sections must use `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8` so the website fills wide desktop displays gracefully while centering content.
3. NO ABSOLUTE POSITIONING FOR LAYOUT: Do not turn the screenshot into a coordinate map. All sections (Hero, Cards, Grids, Footers) must use standard Flexbox and CSS Grid.
4. REFLOW GRIDS: Product cards, categories, and feature grids must reflow across breakpoints:
   - Mobile (375px): 1 or 2 items per row
   - Tablet (768px): 2 or 3 items per row
   - Desktop (1024px - 1440px): 4 or 5 items per row
5. HERO SECTION: 2-column layout on desktop (`lg:grid-cols-2` or `lg:flex-row`), stacked on mobile.
6. ZERO HORIZONTAL OVERFLOW: Ensure no element causes horizontal scrolling on any screen width (375px to 1920px).
{asset_section}{custom_text}
{viewports_desc}"""


def get_refinement_instructions(
    current_code: str,
    discrepancies: str,
    selected_element_html: Optional[str] = None,
) -> str:
    """Generate surgical refinement instructions based on visual and responsive verification."""
    locator_section = ""
    if selected_element_html:
        locator_section = f"""
## Targeted Element (Live DOM Locator)
The user has selected this specific element for update:
```html
{selected_element_html.strip()}
```
Find the corresponding code in the file that renders this element and apply the change specifically there.
"""

    return f"""You are refining an existing front-end implementation to fix visual and responsive discrepancies identified during multi-viewport browser verification.

## Identified Discrepancies & Diagnostic Feedback
{discrepancies.strip()}
{locator_section}
## Responsive Refinement Directives
- If the layout appears as a narrow column on desktop, REMOVE any fixed widths (e.g. `w-[736px]`, `w-[656px]`) and replace with `w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`.
- If absolute positioning was used for content elements, refactor them into clean Flexbox (`flex`) or Grid (`grid`) containers.
- If repeated cards overflow or don't reflow, use responsive breakpoints (`grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5`).
- Ensure no horizontal scrollbar exists on mobile (375px).
- Apply precise, surgical edits without clobbering working sections.
- Output the complete, updated code.
"""
