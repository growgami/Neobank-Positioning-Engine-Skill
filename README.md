# Neobank Positioning Engine

**Find out what your competitors actually claim, what territory they leave open, and exactly how to position against them.**

The Positioning Engine scrapes crypto neobank websites, extracts every positioning signal (headlines, value props, CTAs, proof points, brand voice, and — critically — what they *don't* say), maps the competitive landscape, identifies unclaimed territory, and generates a complete messaging framework with real copy you can use.

This isn't a brand strategy template. Every recommendation traces back to what competitors actually say on their websites and what positioning territory is genuinely unclaimed.

---

## What You Get

A positioning brief covering:

- **Executive Summary** — The one-paragraph strategic read. Where you stand, what's working, what's not, and the single biggest opportunity.
- **Positioning Elements** — For each company analyzed: claims, target audience, benefits, proof points, brand voice, CTA language, and omissions (what they *don't* mention is often more revealing).
- **Territory Map** — Every company scored on four dimensions: audience spectrum (crypto-native vs mainstream), trust model (self-custody vs custodial), value proposition core (yield vs utility), and brand personality (technical vs lifestyle).
- **White Space Analysis** — Positioning territories that are unclaimed or weakly held, with evidence for each.
- **Messaging Framework** — Positioning statements (Geoffrey Moore format), one-liner options, value propositions with proof points, audience-specific messaging, what NOT to say, and competitive response playbooks.

The output is a structured JSON file that renders into a styled HTML/PDF brief.

---

## How It Works

Three stages, fully automated:

```
Scrape  →  Analyze  →  Render
```

1. **Scrape** — A headless browser visits each company's website and pulls positioning data: headlines, subheadlines, meta descriptions, CTAs, body copy, and proof points.
2. **Analyze** — The scraped data is fed to Claude (Anthropic's AI) along with positioning frameworks and competitive intelligence. The AI performs the full analysis: extracting positioning elements, mapping territories, finding white space, and generating the messaging framework.
3. **Render** — The structured brief is rendered as a clean HTML document and PDF.

---

## Getting Started

### Prerequisites

- **Python 3.10+** — [Download Python](https://www.python.org/downloads/) if you don't have it
- **An API key** — Either an [Anthropic API key](https://console.anthropic.com/) or an [OpenRouter API key](https://openrouter.ai/)

### Setup

```bash
# Clone the repo
git clone https://github.com/growgami/neobank-positioning-engine.git
cd neobank-positioning-engine

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Add your API key
cp .env.example .env
# Open .env and paste your ANTHROPIC_API_KEY or OPENROUTER_API_KEY
```

### Run It

**One command, full pipeline:**

```bash
python scripts/run_pipeline.py "KAST" "https://kast.xyz" \
  --competitors "Revolut:https://revolut.com" "Crypto.com:https://crypto.com"
```

This scrapes all websites, runs the analysis, and renders the brief. Output lands in `output/`.

**Or run each stage separately** (useful if you want to re-analyze without re-scraping):

```bash
# Scrape
python scripts/scrape_positioning.py "KAST" "https://kast.xyz"
python scripts/scrape_positioning.py "Revolut" "https://revolut.com"

# Analyze
python scripts/analyze_positioning.py output/kast-positioning.json \
  --competitors revolut

# Render
python scripts/render_positioning.py output/kast-brief.json
```

**Cost:** Each run costs roughly **$0.10–0.35** in API fees, depending on the model and number of competitors.

---

## Using It as a Claude Code Skill

If you use [Claude Code](https://docs.anthropic.com/en/docs/claude-code), the included `SKILL.md` turns the engine into an interactive skill. Claude follows the full workflow with you in the loop — you can steer the analysis, ask follow-up questions, and refine the output before rendering.

```
> position KAST against Revolut and Crypto.com
```

Claude will scrape, analyze, and render, pausing for your input at each stage. This is how the example briefs in this repo were produced.

---

## API Providers

| Provider | Env Variable | Default Model | Cost per Run |
|----------|-------------|---------------|-------------|
| **Anthropic** (recommended) | `ANTHROPIC_API_KEY` | Claude Sonnet 4.5 | ~$0.10–0.20 |
| **OpenRouter** (alternative) | `OPENROUTER_API_KEY` | Claude Sonnet 4.5 | ~$0.15–0.35 |

The engine auto-detects which key is available. Override with `--provider` and `--model` if needed.

---

## Repo Structure

```
neobank-positioning-engine/
├── scripts/
│   ├── scrape_positioning.py     # Website scraper (Playwright)
│   ├── analyze_positioning.py    # LLM-powered positioning analysis
│   ├── render_positioning.py     # HTML/PDF brief renderer
│   └── run_pipeline.py           # Full pipeline runner
├── references/
│   ├── positioning-frameworks.md # Moore, Dunford, territory mapping methodology
│   └── neobank-messaging-map.md  # Pre-researched data on 12+ neobanks
├── examples/
│   ├── kast-brief.json           # Example: KAST vs Revolut, Crypto.com, Wirex
│   └── avici-brief.json          # Example: Avici vs Bleap, KAST, RedotPay
├── SKILL.md                      # Claude Code skill definition
├── requirements.txt
├── .env.example
└── LICENSE
```

---

## Example Output

Two real positioning briefs are included in `examples/`:

**[KAST vs Revolut, Crypto.com, Wirex](examples/kast-brief.json)** — Found that KAST is the only player that is both crypto-native AND spending-first. "Banking without the bank" is punchy but generic. The unclaimed territory: **stablecoin banking** as a category, not just a feature.

**[Avici vs Bleap, KAST, RedotPay](examples/avici-brief.json)** — Found that Avici's self-custodial escrow architecture is genuinely unique, but the homepage buries it under generic "spend crypto easily" messaging. The recommended bet: own **the self-custodial internet neobank** positioning before someone else does.

---

## Built By

**[Growgami](https://growgami.com)** — GTM engineering for crypto and fintech.

We build positioning strategies, landing pages, and go-to-market systems for crypto companies. This engine is one of the tools we use internally and with clients. If you want a positioning audit done for you, or want to talk about your GTM strategy, reach out at [growgami.com](https://growgami.com).

---

## License

MIT — use it, fork it, build on it.
