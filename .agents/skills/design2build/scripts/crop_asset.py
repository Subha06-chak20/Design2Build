"""
Antigravity Skill Helper: Crop Asset
====================================
Invoked by Antigravity to crop a visual asset from a reference screenshot
using normalized [ymin, xmin, ymax, xmax] coordinates (0-1000).
"""

import argparse
import sys
from pathlib import Path

# Add core package to sys.path if not installed in site-packages
try:
    import stc_core
except ImportError:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        core_candidate = current / "screenshot-to-code-core"
        if core_candidate.exists():
            sys.path.insert(0, str(core_candidate))
            break
        current = current.parent

from stc_core.assets import extract_and_save_asset


def main():
    parser = argparse.ArgumentParser(description="Crop asset from screenshot")
    parser.add_argument("screenshot", type=Path, help="Reference screenshot path")
    parser.add_argument("--box", "-b", required=True, help="Coordinates as 'ymin,xmin,ymax,xmax' (0-1000 scale)")
    parser.add_argument("--name", "-n", default="asset", help="Asset name identifier")
    parser.add_argument("--out-dir", "-o", type=Path, default=Path("./assets"), help="Target assets directory")

    args = parser.parse_args()
    coords = [float(x.strip()) for x in args.box.split(",")]
    
    dest = args.out_dir / f"{args.name}.png"
    asset = extract_and_save_asset(args.screenshot, coords, dest, name=args.name)
    if asset:
        print(f"Successfully extracted {args.name} -> {asset.filepath} ({asset.width}x{asset.height}px)")
    else:
        print(f"Failed to extract {args.name}: invalid box or bounds", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
