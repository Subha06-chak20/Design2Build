"""
Headless Browser Screenshot Preview Engine & Responsive Diagnostic Suite
========================================================================
Design2Build Playwright preview rendering backend.
Renders generated HTML in real headless browser viewports:
- Mobile: 375x812
- Tablet: 768x1024
- Desktop: 1024x768 / 1280x832
- Large Desktop: 1440x900
Includes automated responsive health diagnostics:
- Horizontal overflow detection (scrollWidth > innerWidth)
- Artificially narrow container detection on wide viewports
- Uncaught JavaScript runtime errors and console error monitoring
- Native Edge CLI fallback support
"""

import asyncio
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

VIEWPORT_SIZES: Dict[str, Tuple[int, int]] = {
    "mobile": (375, 812),          # Standard modern mobile (iPhone / Android)
    "tablet": (768, 1024),         # Tablet (iPad portrait)
    "desktop": (1024, 768),        # Compact Desktop / Laptop
    "desktop_wide": (1280, 832),   # Standard Desktop (legacy desktop key compatibility)
    "large_desktop": (1440, 900),  # Wide Desktop (modern widescreen)
}

PAGE_LOAD_TIMEOUT_MS = 15000
RENDER_SETTLE_MS = 350

ViewportType = Literal["mobile", "tablet", "desktop", "desktop_wide", "large_desktop", "both", "all"]

# Standard Windows Edge executable paths
EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_system_edge() -> Optional[str]:
    """Locate system Microsoft Edge executable if present."""
    for p in EDGE_PATHS:
        if os.path.isfile(p):
            return p
    return None


@dataclass
class ViewportDiagnostic:
    viewport: str
    width: int
    height: int
    scroll_width: int = 0
    has_horizontal_overflow: bool = False
    main_container_width: Optional[float] = None
    is_artificially_narrow: bool = False
    overflow_elements: List[str] = field(default_factory=list)
    page_errors: List[str] = field(default_factory=list)
    console_errors: List[str] = field(default_factory=list)
    missing_assets: List[str] = field(default_factory=list)
    screenshot_path: Optional[str] = None
    screenshot_bytes: Optional[bytes] = None

    @property
    def is_healthy(self) -> bool:
        return (
            not self.has_horizontal_overflow
            and not self.is_artificially_narrow
            and len(self.page_errors) == 0
        )


class PreviewRenderer:
    """Renders HTML content or files in headless Chromium/Edge and captures screenshots."""

    def __init__(self, prefer_channel: Optional[str] = None):
        self.prefer_channel = prefer_channel
        self._playwright = None
        self._browser = None
        self._lock = asyncio.Lock()

    async def _get_playwright_browser(self):
        from playwright.async_api import async_playwright

        async with self._lock:
            if self._browser is None or not self._browser.is_connected():
                if self._playwright is None:
                    self._playwright = await async_playwright().start()

                # First try default chromium
                try:
                    self._browser = await self._playwright.chromium.launch(
                        headless=True,
                        args=["--no-sandbox", "--disable-gpu"],
                    )
                except Exception:
                    # If chromium binary is missing, attempt msedge channel
                    try:
                        self._browser = await self._playwright.chromium.launch(
                            channel="msedge",
                            headless=True,
                            args=["--no-sandbox", "--disable-gpu"],
                        )
                    except Exception as e:
                        raise RuntimeError(f"Playwright could not launch Chromium or Edge: {e}")

            return self._browser

    async def capture_html(
        self,
        html_content: str,
        viewport: str = "desktop_wide",
        full_page: bool = True,
        output_path: Optional[Union[str, Path]] = None,
    ) -> bytes:
        """Render HTML string and capture screenshot as PNG bytes."""
        width, height = VIEWPORT_SIZES.get(viewport, VIEWPORT_SIZES["desktop_wide"])

        # Try Playwright first
        try:
            browser = await self._get_playwright_browser()
            page = await browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
            )
            try:
                try:
                    await page.set_content(
                        html_content,
                        wait_until="networkidle",
                        timeout=PAGE_LOAD_TIMEOUT_MS,
                    )
                except Exception:
                    pass

                try:
                    await page.evaluate("document.fonts.ready")
                except Exception:
                    pass

                await page.wait_for_timeout(RENDER_SETTLE_MS)
                png_bytes = await page.screenshot(full_page=full_page, type="png")

                if output_path:
                    dest = Path(output_path)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(png_bytes)

                return png_bytes
            finally:
                await page.close()

        except Exception as pw_err:
            # Fallback to system Edge headless CLI
            edge_exe = find_system_edge()
            if not edge_exe:
                raise RuntimeError(f"Failed to render screenshot. Playwright error: {pw_err}. No Edge executable found.")

            return self._capture_with_edge_cli(
                html_content=html_content,
                viewport=viewport,
                output_path=output_path,
                edge_path=edge_exe,
            )

    def _capture_with_edge_cli(
        self,
        html_content: str,
        viewport: str,
        output_path: Optional[Union[str, Path]],
        edge_path: str,
    ) -> bytes:
        """Fallback capture using Edge CLI headless screenshot."""
        width, height = VIEWPORT_SIZES.get(viewport, VIEWPORT_SIZES["desktop_wide"])
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "render.html"
            html_file.write_text(html_content, encoding="utf-8")

            shot_file = Path(output_path) if output_path else Path(tmpdir) / "shot.png"
            shot_file.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                edge_path,
                "--headless=new",
                f"--window-size={width},{height}",
                f"--screenshot={str(shot_file)}",
                "--hide-scrollbars",
                "--disable-gpu",
                html_file.resolve().as_uri(),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return shot_file.read_bytes()

    async def capture_file(
        self,
        file_path: Union[str, Path],
        viewport: str = "desktop_wide",
        full_page: bool = True,
        output_path: Optional[Union[str, Path]] = None,
    ) -> bytes:
        """Render a local HTML file directly via file URI and capture screenshot."""
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")

        width, height = VIEWPORT_SIZES.get(viewport, VIEWPORT_SIZES["desktop_wide"])

        try:
            browser = await self._get_playwright_browser()
            page = await browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
            )
            try:
                try:
                    await page.goto(
                        p.as_uri(),
                        wait_until="networkidle",
                        timeout=PAGE_LOAD_TIMEOUT_MS,
                    )
                except Exception:
                    pass

                try:
                    await page.evaluate("document.fonts.ready")
                except Exception:
                    pass

                await page.wait_for_timeout(RENDER_SETTLE_MS)
                png_bytes = await page.screenshot(full_page=full_page, type="png")

                if output_path:
                    dest = Path(output_path)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(png_bytes)

                return png_bytes
            finally:
                await page.close()
        except Exception as pw_err:
            edge_exe = find_system_edge()
            if not edge_exe:
                raise RuntimeError(f"Failed to render screenshot. Playwright error: {pw_err}. No Edge executable found.")

            shot_file = Path(output_path) if output_path else Path(tempfile.gettempdir()) / "shot.png"
            shot_file.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                edge_exe,
                "--headless=new",
                f"--window-size={width},{height}",
                f"--screenshot={str(shot_file)}",
                "--hide-scrollbars",
                "--disable-gpu",
                p.as_uri(),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return shot_file.read_bytes()

    async def inspect_viewport_diagnostics(
        self,
        html_or_file: Union[str, Path],
        viewport: str = "desktop_wide",
        output_path: Optional[Union[str, Path]] = None,
        full_page: bool = True,
    ) -> ViewportDiagnostic:
        """Render page, capture screenshot, and extract comprehensive responsive health diagnostics."""
        width, height = VIEWPORT_SIZES.get(viewport, VIEWPORT_SIZES["desktop_wide"])
        diagnostic = ViewportDiagnostic(viewport=viewport, width=width, height=height)

        browser = await self._get_playwright_browser()
        page = await browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
        )

        page.on("pageerror", lambda err: diagnostic.page_errors.append(str(err)))
        page.on("console", lambda msg: diagnostic.console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("requestfailed", lambda req: diagnostic.missing_assets.append(f"{req.url}: {req.failure}"))

        try:
            if isinstance(html_or_file, Path) or (isinstance(html_or_file, str) and os.path.isfile(str(html_or_file))):
                file_uri = Path(html_or_file).resolve().as_uri()
                await page.goto(file_uri, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
            else:
                await page.set_content(str(html_or_file), wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)

            try:
                await page.evaluate("document.fonts.ready")
            except Exception:
                pass

            await page.wait_for_timeout(RENDER_SETTLE_MS)

            # In-page responsive health audit
            js_metrics = await page.evaluate(
                """() => {
                    const scrollW = document.documentElement.scrollWidth;
                    const innerW = window.innerWidth;
                    const hasOverflow = scrollW > (innerW + 2);

                    // Find main content container
                    const candidates = Array.from(document.querySelectorAll('main, #root > div, body > div'));
                    let maxContainerW = 0;
                    for (const el of candidates) {
                        const w = el.getBoundingClientRect().width;
                        if (w > maxContainerW) maxContainerW = w;
                    }
                    if (maxContainerW === 0) maxContainerW = innerW;

                    // Narrow container check on wide screens:
                    // If desktop viewport (>=1280px) has main container < 850px without explicit intent
                    const isNarrow = (innerW >= 1280) && (maxContainerW < 850);

                    // Elements overflowing screen edge
                    const overflowing = [];
                    const allEls = document.querySelectorAll('*');
                    for (const el of allEls) {
                        const rect = el.getBoundingClientRect();
                        if (rect.right > (innerW + 4) && rect.width > 0 && rect.height > 0) {
                            const tag = el.tagName.toLowerCase();
                            const cls = (el.className && typeof el.className === 'string') ? el.className.split(' ').slice(0, 2).join('.') : '';
                            const id = el.id ? '#' + el.id : '';
                            overflowing.push(`${tag}${id}${cls ? '.' + cls : ''}`);
                            if (overflowing.length >= 5) break;
                        }
                    }

                    return {
                        scroll_width: scrollW,
                        has_horizontal_overflow: hasOverflow,
                        main_container_width: Math.round(maxContainerW),
                        is_artificially_narrow: isNarrow,
                        overflow_elements: overflowing
                    };
                }"""
            )

            diagnostic.scroll_width = js_metrics["scroll_width"]
            diagnostic.has_horizontal_overflow = js_metrics["has_horizontal_overflow"]
            diagnostic.main_container_width = js_metrics["main_container_width"]
            diagnostic.is_artificially_narrow = js_metrics["is_artificially_narrow"]
            diagnostic.overflow_elements = js_metrics["overflow_elements"]

            png_bytes = await page.screenshot(full_page=full_page, type="png")
            diagnostic.screenshot_bytes = png_bytes

            if output_path:
                dest = Path(output_path)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(png_bytes)
                diagnostic.screenshot_path = str(dest.resolve())

            return diagnostic
        finally:
            await page.close()

    async def capture_responsive_suite(
        self,
        html_or_file: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        viewports: Tuple[str, ...] = ("mobile", "tablet", "desktop", "large_desktop"),
    ) -> Dict[str, ViewportDiagnostic]:
        """Capture screenshots and responsive health diagnostics across a suite of screen sizes."""
        out_dir = Path(output_dir) if output_dir else None
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)

        results: Dict[str, ViewportDiagnostic] = {}

        for vp in viewports:
            out_path = out_dir / f"preview_{vp}_{VIEWPORT_SIZES[vp][0]}.png" if out_dir else None
            diag = await self.inspect_viewport_diagnostics(
                html_or_file=html_or_file,
                viewport=vp,
                output_path=out_path,
            )
            results[vp] = diag

        return results

    async def capture_both_viewports(
        self,
        html_or_file: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, bytes]:
        """Capture both desktop (1280x832) and mobile (375x812) previews."""
        out_dir = Path(output_dir) if output_dir else None
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)

        desktop_path = out_dir / "preview_desktop.png" if out_dir else None
        mobile_path = out_dir / "preview_mobile.png" if out_dir else None

        if isinstance(html_or_file, Path) or (isinstance(html_or_file, str) and os.path.isfile(html_or_file)):
            file_path = Path(html_or_file).resolve()
            desktop_bytes = await self.capture_file(file_path, viewport="desktop_wide", output_path=desktop_path)
            mobile_bytes = await self.capture_file(file_path, viewport="mobile", output_path=mobile_path)
        else:
            content = str(html_or_file)
            desktop_bytes = await self.capture_html(content, viewport="desktop_wide", output_path=desktop_path)
            mobile_bytes = await self.capture_html(content, viewport="mobile", output_path=mobile_path)

        return {
            "desktop": desktop_bytes,
            "mobile": mobile_bytes,
        }

    async def close(self):
        """Clean up browser resources."""
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
