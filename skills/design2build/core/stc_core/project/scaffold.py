"""
Project Workspace Scaffolding and Asset Bundler
==============================================
Preserved and adapted from abi/screenshot-to-code's export architecture.
Scaffolds local project directories, localizes extracted assets into ./assets/,
and generates self-contained, reproducible websites.
"""

import base64
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from stc_core.config import ProjectConfig

from bs4 import BeautifulSoup


def initialize_project_directory(target_dir: Path) -> Tuple[Path, Path]:
    """Create project workspace and its assets subdirectory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = target_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return target_dir, assets_dir


def localize_data_urls_in_html(html_content: str, assets_dir: Path) -> str:
    """Find any embedded base64 data URLs in <img> or background styles and save them as local assets."""
    soup = BeautifulSoup(html_content, "html.parser")
    counter = 1

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src.startswith("data:image/") and "," in src:
            header, encoded = src.split(",", 1)
            mime = header.split(";")[0].removeprefix("data:")
            ext = "png"
            if "jpeg" in mime or "jpg" in mime:
                ext = "jpg"
            elif "svg" in mime:
                ext = "svg"
            elif "webp" in mime:
                ext = "webp"

            filename = f"image_{counter}.{ext}"
            file_path = assets_dir / filename
            try:
                raw_bytes = base64.b64decode(encoded)
                file_path.write_bytes(raw_bytes)
                img["src"] = f"./assets/{filename}"
                counter += 1
            except Exception:
                pass

    return str(soup)


def scaffold_project(
    target_dir: Path,
    html_content: str,
    stack: str = "html_tailwind",
    extracted_assets: Optional[Dict[str, str]] = None,
    config: Optional["ProjectConfig"] = None,
) -> Path:
    """
    Write project files into target directory.
    Creates index.html, saves assets, and adds project config and run runners.
    """
    proj_dir, assets_dir = initialize_project_directory(target_dir)

    # Localize any inline data URLs
    clean_html = localize_data_urls_in_html(html_content, assets_dir)

    index_file = proj_dir / "index.html"
    index_file.write_text(clean_html, encoding="utf-8")

    # Save ProjectConfig if provided
    if config:
        config.save(proj_dir / "d2b.config.json")

    # Generate quick local dev server runner
    server_script = proj_dir / "serve.py"
    server_script.write_text(
        """import http.server
import socketserver
import webbrowser
import sys

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

print(f"Serving at http://localhost:{PORT}")
try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        webbrowser.open(f"http://localhost:{PORT}")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\\nServer stopped.")
    sys.exit(0)
""",
        encoding="utf-8",
    )

    # Determine run instructions
    run_instructions = """## How to run locally
Run the local dev server:
```bash
python serve.py
```
Or with Node:
```bash
npx serve .
```
Or open directly:
```bash
# Double-click index.html or open via browser
```"""
    if config and config.run_mode.value == "static":
        run_instructions = """## How to run locally
This is a purely static project. Open `index.html` directly in your browser:
```bash
# Double-click index.html
```
Or run the optional preview server:
```bash
python serve.py
```"""
    elif config and config.run_mode.value == "vite_dev":
        run_instructions = """## How to run locally
Start the local development server:
```bash
npm install
npm run dev
```
Or view the standalone preview directly via `index.html`."""

    project_type_info = f"- **Type**: `{config.project_type.value}`\n" if config else ""
    devices_info = f"- **Devices**: `{config.target_devices.value}`\n" if config else ""

    # Generate README in project directory
    readme_file = proj_dir / "README.md"
    readme_file.write_text(
        f"""# Generated Front-End Project

Created with Design2Build visual coding workflow.
- **Stack**: `{config.stack if (config and config.stack) else stack}`
{project_type_info}{devices_info}- **Entry point**: `index.html`
- **Assets**: `./assets/`

{run_instructions}
""",
        encoding="utf-8",
    )

    return index_file

