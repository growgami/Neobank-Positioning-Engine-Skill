# Neobank Positioning Engine

## Run Commands

| Phase         | Command                                                                                        |
| ------------- | ---------------------------------------------------------------------------------------------- |
| Scrape        | `python scripts/scrape_positioning.py "Company" "https://url.com"`                             |
| Analyze       | `python scripts/analyze_positioning.py output/slug-positioning.json --competitors comp1 comp2` |
| Render        | `python scripts/render_positioning.py output/slug-brief.json`                                  |
| Full pipeline | `python scripts/run_pipeline.py "Company" "https://url.com" --competitors "Comp:https://url"`  |

## Environment Setup

```bash
# Create virtualenv
python -m venv .venv && source .venv/bin/activate

# Install system deps (macOS)
brew install pango cairo gdk-pixbuf libffi

# Install system deps (Ubuntu/Debian)
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi-dev

# Install Python deps
pip install -r requirements.txt
playwright install chromium
```

## API Key Configuration

```bash
cp .env.example .env
# Edit .env and set at least one:
# ANTHROPIC_API_KEY=sk-ant-...   (preferred, ~$0.10-0.20/run)
# OPENROUTER_API_KEY=sk-or-...   (fallback, ~$0.15-0.35/run)
```

Auto-detection order: Anthropic key → OpenRouter key. Override with `--provider anthropic|openrouter` and `--model <model-id>`.

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

## Common Issues

| Issue                        | Fix                                                                                 |
| ---------------------------- | ----------------------------------------------------------------------------------- |
| `WeasyPrint` import error    | Install system deps: `brew install pango cairo` (macOS) or apt-get equivalents      |
| Playwright browser not found | `playwright install chromium`                                                       |
| Scraper returns empty body   | Site uses heavy JS — increase `asyncio.sleep` in `scrape_page()` or add manual data |
| API auth error               | Check `.env` exists and key has no trailing whitespace                              |
| `output/` not found          | Scripts create it automatically on first run                                        |
| PDF blank / CSS broken       | WeasyPrint version mismatch — pin to `weasyprint~=63.0`                             |

## Linting

```bash
pip install ruff mypy
ruff check scripts/
mypy scripts/ --ignore-missing-imports
```
