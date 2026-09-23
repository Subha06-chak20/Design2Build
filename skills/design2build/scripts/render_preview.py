"""
Design2Build Helper: Render Preview
====================================
Invoked by AI agents to render an HTML file in headless browser and capture PNG screenshots.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add core package to sys.path if not installed in site-packages
try:
    import d2b_core
except ImportError:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        core_candidate = current / "core"
        if core_candidate.exists():
            sys.path.insert(0, str(core_candidate))
            break
        current = current.parent

from d2b_core.preview import PreviewRenderer


async def main():
    parser = argparse.ArgumentParser(description="Render HTML to screenshot PNG")
    parser.add_argument("html_file", type=Path, help="Path to index.html")
    parser.add_argument("--out", "-o", type=Path, default=Path("preview.png"), help="Output PNG path")
    parser.add_argument("--viewport", "-v", choices=["desktop", "mobile", "both"], default="desktop", help="Viewport")

    args = parser.parse_args()
    renderer = PreviewRenderer()

    try:
        if args.viewport == "both":
            out_dir = args.out.parent if args.out.suffix else args.out
            res = await renderer.capture_both_viewports(args.html_file, output_dir=out_dir)
            print(f"Captured desktop ({len(res['desktop'])} bytes) and mobile ({len(res['mobile'])} bytes)")
        else:
            png_bytes = await renderer.capture_file(args.html_file, viewport=args.viewport, output_path=args.out)
            print(f"Captured {args.viewport} screenshot: {args.out} ({len(png_bytes)} bytes)")
    finally:
        await renderer.close()


if __name__ == "__main__":
    asyncio.run(main())
