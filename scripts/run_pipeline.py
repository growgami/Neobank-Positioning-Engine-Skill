"""
Positioning Pipeline Runner

Usage:
    python scripts/run_pipeline.py "KAST" "https://kast.xyz" --competitors "Revolut:https://revolut.com" "Crypto.com:https://crypto.com"

Chains all three stages: scrape → analyze → render.
Uses subprocess so each script runs independently with its own argument parsing.
"""

import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output"

SCRAPER = SCRIPT_DIR / "scrape_positioning.py"
ANALYZER = SCRIPT_DIR / "analyze_positioning.py"
RENDERER = SCRIPT_DIR / "render_positioning.py"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def run(cmd: list[str], label: str, allow_fail: bool = False) -> bool:
    print(f"\n{'=' * 60}")
    print(f"[{label}] {' '.join(cmd)}")
    print("=" * 60)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        if allow_fail:
            print(f"Warning: {label} failed (exit {result.returncode}), continuing...")
            return False
        else:
            print(f"Error: {label} failed (exit {result.returncode}), aborting.")
            sys.exit(result.returncode)
    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the full positioning pipeline: scrape → analyze → render"
    )
    parser.add_argument("company", help='Company name (e.g. "KAST")')
    parser.add_argument("url", help='Company website URL (e.g. "https://kast.xyz")')
    parser.add_argument(
        "--competitors",
        nargs="*",
        default=[],
        help='Competitors as "Name:URL" pairs (e.g. "Revolut:https://revolut.com")',
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model to pass to the analyzer",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openrouter"],
        default=None,
        help="API provider to pass to the analyzer",
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping (use existing output files)",
    )
    args = parser.parse_args()

    python = sys.executable
    slug = slugify(args.company)

    # Parse competitor pairs
    competitors = []
    for comp in args.competitors:
        if ":" in comp:
            name, url = comp.split(":", 1)
            competitors.append((name.strip(), url.strip()))
        else:
            print(f"Warning: competitor '{comp}' missing URL (expected 'Name:URL'), skipping")

    # Stage 1: Scrape
    if not args.skip_scrape:
        # Scrape target
        run(
            [python, str(SCRAPER), args.company, args.url],
            f"Scrape {args.company}",
        )

        # Scrape competitors (failures are non-fatal)
        for name, url in competitors:
            run(
                [python, str(SCRAPER), name, url],
                f"Scrape {name}",
                allow_fail=True,
            )
    else:
        print("Skipping scrape stage (--skip-scrape)")

    # Stage 2: Analyze
    target_json = OUTPUT_DIR / f"{slug}-positioning.json"
    if not target_json.exists():
        print(f"Error: expected scraped data at {target_json}")
        sys.exit(1)

    competitor_slugs = [slugify(name) for name, _ in competitors]
    # Only include competitors whose scraped data exists
    existing_slugs = [s for s in competitor_slugs if (OUTPUT_DIR / f"{s}-positioning.json").exists()]

    analyze_cmd = [python, str(ANALYZER), str(target_json)]
    if existing_slugs:
        analyze_cmd.extend(["--competitors"] + existing_slugs)
    if args.model:
        analyze_cmd.extend(["--model", args.model])
    if args.provider:
        analyze_cmd.extend(["--provider", args.provider])

    run(analyze_cmd, "Analyze positioning")

    # Stage 3: Render
    brief_json = OUTPUT_DIR / f"{slug}-brief.json"
    if not brief_json.exists():
        print(f"Error: expected brief at {brief_json}")
        sys.exit(1)

    run(
        [python, str(RENDERER), str(brief_json)],
        "Render brief",
    )

    print(f"\n{'=' * 60}")
    print("Pipeline complete!")
    print(f"  Scraped data: {OUTPUT_DIR / f'{slug}-positioning.json'}")
    print(f"  Brief JSON:   {brief_json}")
    print(f"  HTML/PDF:     {OUTPUT_DIR / f'{slug}-positioning-brief.html'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
