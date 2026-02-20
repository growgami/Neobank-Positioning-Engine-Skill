# Neobank Positioning Engine

Scrapes crypto neobank websites, maps the competitive landscape, finds unclaimed positioning territory, and generates a complete messaging framework with real copy.

Not a brand strategy template. Every output is grounded in what competitors actually say, what users actually complain about, and what territory is genuinely unclaimed.

## What It Does

Give it a company name and its competitors. It will:

1. **Scrape** positioning data from each company's website (headlines, value props, CTAs, proof points, brand voice)
2. **Analyze** positioning elements via an LLM: extract claims, map territories, find white space
3. **Generate** a full messaging framework: positioning statements, one-liners, value props, audience-specific copy, what not to say, competitive responses
4. **Render** everything as a styled HTML/PDF brief

## Quick Start

### Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and add at least one API key:

```bash
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY or OPENROUTER_API_KEY
```

### Two Ways to Use It

#### Path A: Automated Pipeline (API-powered)

Run the full pipeline in one command:

```bash
python scripts/run_pipeline.py "KAST" "https://kast.xyz" \
  --competitors "Revolut:https://revolut.com" "Crypto.com:https://crypto.com"
```

Or run each stage separately:

```bash
# 1. Scrape target and competitors
python scripts/scrape_positioning.py "KAST" "https://kast.xyz"
python scripts/scrape_positioning.py "Revolut" "https://revolut.com"
python scripts/scrape_positioning.py "Crypto.com" "https://crypto.com"

# 2. Analyze (calls Claude API to generate the brief)
python scripts/analyze_positioning.py output/kast-positioning.json \
  --competitors revolut crypto-com

# 3. Render HTML/PDF
python scripts/render_positioning.py output/kast-brief.json
```

**Cost:** ~$0.10-0.35 per run depending on model and number of competitors.

#### Path B: Claude Code Skill (interactive)

If you use [Claude Code](https://docs.anthropic.com/en/docs/claude-code), the `SKILL.md` file turns this into an interactive skill. Claude follows the full workflow — scraping, analysis, and rendering — with you in the loop.

Tell Claude:
- `position [neobank name]`
- `positioning audit for [neobank name]`
- `competitive positioning: [neobank A] vs [neobank B] vs [neobank C]`

Claude runs the scraper, reads the data, performs the analysis conversationally (you can steer it), and renders the output.

## API Providers

The analyzer supports two providers:

| Provider | Env Variable | Default Model | Notes |
|----------|-------------|---------------|-------|
| **Anthropic** (default) | `ANTHROPIC_API_KEY` | `claude-sonnet-4-5-20250514` | Direct API, lowest latency |
| **OpenRouter** (fallback) | `OPENROUTER_API_KEY` | `anthropic/claude-sonnet-4-5-20250514` | Access to many models |

The analyzer auto-detects which key is available. Anthropic is preferred when both are set. Override with `--provider` and `--model` flags.

## What's Inside

| File | Purpose |
|------|---------|
| `scripts/scrape_positioning.py` | Browser-based scraper for positioning data extraction |
| `scripts/analyze_positioning.py` | LLM-powered analysis: extracts positioning, maps territory, generates framework |
| `scripts/render_positioning.py` | HTML/PDF renderer for the final brief |
| `scripts/run_pipeline.py` | Convenience wrapper that chains scrape → analyze → render |
| `SKILL.md` | Claude Code skill definition (interactive workflow) |
| `references/positioning-frameworks.md` | Moore, Dunford, territory mapping, competitive response patterns |
| `references/neobank-messaging-map.md` | Pre-researched positioning data for 10+ neobanks and exchanges |
| `examples/kast-brief.json` | Example output brief (KAST vs Revolut, Crypto.com, Wirex) |

## Output

The engine produces a structured brief containing:

- **Executive summary** — the one-paragraph strategic read
- **Positioning elements** — for each company: claims, audience, benefits, proof, voice, omissions
- **Territory map** — companies plotted on four dimensions (audience spectrum, trust model, value core, brand personality)
- **White space** — unclaimed positioning territories with rationale
- **Messaging framework** — positioning statements, one-liners, value props, audience-specific copy, what not to say, competitive responses

See `examples/kast-brief.json` for the full schema.

## References

The `references/` folder contains two research docs used as context:

**positioning-frameworks.md** — Moore's positioning statement format, Dunford's five-component framework, territory mapping methodology, common overused claims to avoid, messaging hierarchy, and competitive response patterns.

**neobank-messaging-map.md** — Pre-researched positioning data for KAST, Bleap, Hi, Wirex, RedotPay, Revolut, Nubank, Cash App, N26, Crypto.com, Coinbase, and Bybit MyBank. Includes dimension scores and six unclaimed positioning territories.

## Built By

[Growgami](https://growgami.com). GTM engineering for crypto and fintech.

## License

MIT
