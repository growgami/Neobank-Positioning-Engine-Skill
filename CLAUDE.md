# Neobank Positioning Engine

## Build/Run
- Install: `pip install -r requirements.txt && playwright install chromium`
- Scrape: `python scripts/scrape_positioning.py "Company" "https://url.com"`
- Analyze: `python scripts/analyze_positioning.py output/slug-positioning.json --competitors comp1 comp2`
- Render: `python scripts/render_positioning.py output/slug-brief.json`
- Pipeline: `python scripts/run_pipeline.py "Company" "https://url.com" --competitors "Comp:https://url"`

## Architecture
Three-stage pipeline: scrape (Playwright) → analyze (Claude API) → render (WeasyPrint).
Scripts in `scripts/`, references in `references/`, examples in `examples/`, output in `output/`.
Brief schema defined by `examples/kast-brief.json`.

## Key Patterns
- Scripts use `sys.argv` / `argparse` at module level with `if __name__ == "__main__"` guards
- `run_pipeline.py` chains scripts via `subprocess.run()` (not imports) because of asyncio + argv patterns
- `analyze_positioning.py` auto-detects API provider from env vars (Anthropic preferred, OpenRouter fallback)
- `.env` loaded by a simple parser in `analyze_positioning.py`, no dotenv dependency
- `slugify()` is duplicated across scripts intentionally (no shared utils module)
