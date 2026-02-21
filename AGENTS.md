# AGENTS.md — Neobank Positioning Engine Skill

## How Claude Code Invokes This Skill

Claude Code reads `SKILL.md` at session start. The skill triggers on phrases like:

- `position [company]`
- `positioning audit for [company]`
- `competitive positioning: A vs B vs C`

Claude then drives the three-script pipeline interactively, pausing for human input at defined checkpoints.

---

## Invocation Pattern

```
Trigger phrase → Phase 1 (Scrape) → [PAUSE] → Phase 2 (Analyze) → [PAUSE] → Phase 3 (Render) → Done
```

Claude calls scripts via `subprocess`-style Bash tool calls — it does NOT import them as modules.

---

## Pause Points (Human Review Required)

| After Phase | What Claude Shows                           | What Human Decides                                  |
| ----------- | ------------------------------------------- | --------------------------------------------------- |
| Scrape      | List of URLs scraped + data quality summary | Approve data, add missing competitors, or re-scrape |
| Analyze     | Positioning map + white space findings      | Confirm strategic direction before generating copy  |
| Render      | PDF path + brief summary                    | Accept output or request revisions to framework     |

Claude MUST stop and surface results at each pause point. Do not auto-chain all three stages without human confirmation.

---

## Error Handling Expectations

| Error                                         | Expected Behavior                                                                        |
| --------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Playwright scrape fails (bot protection, 403) | Fall back to `references/neobank-messaging-map.md`, note fallback in output              |
| Thin scrape data (<200 chars body text)       | Warn user, suggest manual input or app store description as supplement                   |
| API key missing                               | Exit with clear message: "Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY in .env"           |
| API rate limit / timeout                      | Retry once (MAX_RETRIES=1), then surface error with raw scraped data for manual analysis |
| WeasyPrint missing system deps                | Output HTML only, note PDF generation failed with install instructions                   |
| `output/` directory missing                   | Scripts create it automatically — not an error                                           |

---

## Output Contract

`analyze_positioning.py` MUST emit JSON matching the schema in `examples/kast-brief.json`. Fields:

```
company, date, competitors[], executive_summary,
positioning_elements{}, territory_map{}, white_space[],
messaging_framework{
  positioning_statements[], one_liners[], value_propositions[],
  audience_messaging[], what_not_to_say[], competitive_responses[]
}
```

`render_positioning.py` reads this schema. Breaking changes to the schema break rendering.

---

## Custom Framework Adaptation

To adapt this skill for non-neobank verticals:

1. **References** — Replace `references/neobank-messaging-map.md` with pre-mapped data for the new vertical. Keep `references/positioning-frameworks.md` (Moore/Dunford frameworks are universal).

2. **Territory dimensions** — The four dimensions (audience spectrum, trust model, value prop core, brand personality) are defined in the analyze prompt inside `scripts/analyze_positioning.py`. Search for `POSITIONING_DIMENSIONS` or equivalent prompt section and rewrite for your vertical.

3. **Scrape targets** — `scrape_positioning.py` scrapes generic web content — no neobank-specific logic. Works for any B2C website.

4. **Skill trigger** — Update `SKILL.md` front matter `description` field and trigger phrases in the `## Trigger` section.

5. **Examples** — Add a real brief JSON to `examples/` for the new vertical so Claude has a concrete output reference.

No code changes required for new competitors — they're passed as CLI arguments.

---

## Running Outside Claude Code

The skill scripts are plain Python. Any agent or CI system can invoke them:

```bash
# Full pipeline (non-interactive)
python scripts/run_pipeline.py "Company" "https://url.com" \
  --competitors "Rival1:https://r1.com" "Rival2:https://r2.com"

# Stage by stage
python scripts/scrape_positioning.py "Company" "https://url.com"
python scripts/analyze_positioning.py output/company-positioning.json --competitors rival1 rival2
python scripts/render_positioning.py output/company-brief.json
```

All scripts exit 0 on success, non-zero on failure. Errors go to stderr.
