# Neobank Positioning Engine

> **Install as an agent skill:** `npx skills add growgami/Neobank-Positioning-Engine-Skill`

**Find out what your competitors actually claim, what territory they leave open, and exactly how to position against them.**

The Positioning Engine scrapes crypto neobank websites, extracts every positioning signal (headlines, value props, CTAs, proof points, brand voice, and — critically — what they _don't_ say), maps the competitive landscape, identifies unclaimed territory, and generates a complete messaging framework with real copy you can use.

This isn't a brand strategy template. Every recommendation traces back to what competitors actually say on their websites and what positioning territory is genuinely unclaimed.

---

## Architecture

```mermaid
flowchart LR
    subgraph Phase1["Phase 1 — Scrape"]
        S1[scrape_positioning.py\nPlaywright headless browser]
        S1 -->|output/{slug}-positioning.json| D1[(Positioning\nJSON)]
    end

    subgraph Phase2["Phase 2 — Analyze"]
        D1 --> A1[analyze_positioning.py\nClaude API]
        REF[references/\nFrameworks + Map] --> A1
        A1 -->|output/{slug}-brief.json| D2[(Brief\nJSON)]
    end

    subgraph Phase3["Phase 3 — Render"]
        D2 --> R1[render_positioning.py\nWeasyPrint]
        R1 --> PDF[output/{slug}-brief.pdf]
        R1 --> HTML[output/{slug}-brief.html]
    end

    Phase1 --> Phase2 --> Phase3
```

`run_pipeline.py` chains all three stages in one command via `subprocess.run()`.

---

## What You Get

A positioning brief covering:

- **Executive Summary** — The one-paragraph strategic read. Where you stand, what's working, what's not, and the single biggest opportunity.
- **Positioning Elements** — For each company analyzed: claims, target audience, benefits, proof points, brand voice, CTA language, and omissions (what they _don't_ mention is often more revealing).
- **Territory Map** — Every company scored on four dimensions: audience spectrum (crypto-native vs mainstream), trust model (self-custody vs custodial), value proposition core (yield vs utility), and brand personality (technical vs lifestyle).
- **White Space Analysis** — Positioning territories that are unclaimed or weakly held, with evidence for each.
- **Messaging Framework** — Positioning statements (Geoffrey Moore format), one-liner options, value propositions with proof points, audience-specific messaging, what NOT to say, and competitive response playbooks.

The output is a structured JSON file that renders into a styled HTML/PDF brief.

---

## Installation

### System Dependencies

WeasyPrint requires native libraries. Install before `pip install`.

**macOS:**

```bash
brew install pango cairo gdk-pixbuf libffi
```

**Ubuntu / Debian:**

```bash
sudo apt-get install -y \
  libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \
  libffi-dev libjpeg-dev libopenjp2-7
```

**Windows:** Use WSL2 with the Ubuntu instructions above.

### Python Setup

```bash
git clone https://github.com/growgami/Neobank-Positioning-Engine-Skill.git
cd Neobank-Positioning-Engine-Skill

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

| Variable             | Required       | Description                                       |
| -------------------- | -------------- | ------------------------------------------------- |
| `ANTHROPIC_API_KEY`  | One of the two | Direct Anthropic API — preferred. ~$0.10–0.20/run |
| `OPENROUTER_API_KEY` | One of the two | OpenRouter fallback. ~$0.15–0.35/run              |

The engine auto-detects which key is available (Anthropic takes priority). Override with `--provider` and `--model` flags.

---

## Usage

### Full Pipeline (one command)

```bash
python scripts/run_pipeline.py "KAST" "https://kast.xyz" \
  --competitors "Revolut:https://revolut.com" "Crypto.com:https://crypto.com"
```

Output lands in `output/kast-brief.json` and `output/kast-brief.pdf`.

### Stage by Stage

```bash
# 1. Scrape target + each competitor
python scripts/scrape_positioning.py "KAST" "https://kast.xyz"
python scripts/scrape_positioning.py "Revolut" "https://revolut.com"
python scripts/scrape_positioning.py "Crypto.com" "https://crypto.com"

# 2. Analyze (re-run without re-scraping to iterate on analysis)
python scripts/analyze_positioning.py output/kast-positioning.json \
  --competitors revolut crypto-com

# 3. Render to PDF
python scripts/render_positioning.py output/kast-brief.json
```

Running stages separately is useful when you want to re-analyze with different instructions without re-scraping (scraping is slow; analysis is fast).

### Optional Flags

| Flag         | Values                    | Default                      |
| ------------ | ------------------------- | ---------------------------- |
| `--provider` | `anthropic`, `openrouter` | auto-detected from env       |
| `--model`    | any model ID              | `claude-sonnet-4-5-20250514` |

---

## Output Format

`output/{slug}-brief.json` — matches the schema in `examples/kast-brief.json`:

```json
{
  "company": "KAST",
  "date": "2026-02-17",
  "competitors": ["Revolut", "Crypto.com"],
  "executive_summary": "...",
  "positioning_elements": { "KAST": { ... }, "Revolut": { ... } },
  "territory_map": { "dimensions": [...], "scores": { ... } },
  "white_space": [ { "territory": "...", "evidence": "..." } ],
  "messaging_framework": {
    "positioning_statements": [...],
    "one_liners": [...],
    "value_propositions": [...],
    "audience_messaging": [...],
    "what_not_to_say": [...],
    "competitive_responses": [...]
  }
}
```

`render_positioning.py` converts this to `output/{slug}-brief.html` and `output/{slug}-brief.pdf`.

---

## Cost

| Provider                | Model             | Cost per Run |
| ----------------------- | ----------------- | ------------ |
| Anthropic (recommended) | Claude Sonnet 4.5 | ~$0.10–0.20  |
| OpenRouter              | Claude Sonnet 4.5 | ~$0.15–0.35  |

Cost scales with the number of competitors (more scraped content = more tokens). 3–5 competitors is the typical range.

---

## Install as an Agent Skill

Add the skill to any supported AI coding agent ([40+ supported](https://github.com/vercel-labs/skills)):

```bash
npx skills add growgami/Neobank-Positioning-Engine-Skill
```

If you use [Claude Code](https://docs.anthropic.com/en/docs/claude-code), the included `SKILL.md` turns the engine into an interactive skill. Claude follows the full workflow with you in the loop — you can steer the analysis, ask follow-up questions, and refine the output before rendering.

```
> position KAST against Revolut and Crypto.com
```

Claude will scrape, analyze, and render, pausing for your input at each stage. This is how the example briefs in this repo were produced.

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
├── .github/workflows/ci.yml      # Ruff, mypy, syntax + dep install checks
├── SKILL.md                      # Claude Code skill definition
├── CLAUDE.md                     # Dev environment and run commands
├── AGENTS.md                     # Agent invocation guide and error handling
├── pyproject.toml                # Project metadata, ruff + mypy config
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
