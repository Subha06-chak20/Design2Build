"""
Design2Build Helper: Diff Preview
==================================
Invoked by AI agents to compute visual difference and generate side-by-side composites.
"""

import argparse
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

from d2b_core.verification import compute_visual_difference


def main():
    parser = argparse.ArgumentParser(description="Compare reference and rendered screenshots")
    parser.add_argument("reference", type=Path, help="Path to reference screenshot")
    parser.add_argument("rendered", type=Path, help="Path to rendered screenshot")
    parser.add_argument("--diff", type=Path, help="Output path for diff image")
    parser.add_argument("--composite", type=Path, help="Output path for composite image")

    args = parser.parse_args()
    res = compute_visual_difference(
        args.reference,
        args.rendered,
        output_diff_path=args.diff,
        output_composite_path=args.composite,
    )

    print(f"Similarity Score: {round(res.similarity_score * 100, 1)}%")
    print(f"Discrepancy     : {res.difference_percentage}%")
    if res.composite_image_path:
        print(f"Composite image : {res.composite_image_path}")


if __name__ == "__main__":
    main()
