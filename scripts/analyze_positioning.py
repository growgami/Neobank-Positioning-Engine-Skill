"""
Positioning Brief Analyzer

Usage:
    python scripts/analyze_positioning.py output/kast-positioning.json --competitors revolut crypto-com

Takes scraped JSON from scrape_positioning.py, calls an LLM to extract positioning
elements, map territories, find white space, and generate a messaging framework.
Outputs a structured brief JSON matching the kast-brief.json schema.

Requires: pip install anthropic openai
Auth: Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY in environment / .env
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output"
REFERENCES_DIR = PROJECT_DIR / "references"
EXAMPLES_DIR = PROJECT_DIR / "examples"

DEFAULT_MODEL_ANTHROPIC = "claude-sonnet-4-5-20250514"
DEFAULT_MODEL_OPENROUTER = "anthropic/claude-sonnet-4-5-20250514"
MAX_BODY_CHARS_PER_PAGE = 2000
MAX_RETRIES = 1


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_env():
    """Load .env file if present (simple key=value parser, no dependency)."""
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def load_text_file(path: Path) -> str:
    if not path.exists():
        print(f"Warning: {path} not found, skipping")
        return ""
    return path.read_text(encoding="utf-8")


def load_context_files() -> dict:
    """Load SKILL.md (phases 2-5 only) and reference files."""
    skill_text = load_text_file(PROJECT_DIR / "SKILL.md")

    # Extract phases 2-5 from SKILL.md
    phases_text = ""
    if skill_text:
        # Find from Phase 2 through end of Phase 5 (before Phase 6)
        match = re.search(
            r"(### Phase 2: Extract Positioning Elements.*?)(?=### Phase 6:|## Rules|$)",
            skill_text,
            re.DOTALL,
        )
        if match:
            phases_text = match.group(1).strip()
        else:
            # Fallback: use everything after Phase 1
            match = re.search(r"(### Phase 2:.*)", skill_text, re.DOTALL)
            if match:
                phases_text = match.group(1).strip()

    frameworks = load_text_file(REFERENCES_DIR / "positioning-frameworks.md")
    messaging_map = load_text_file(REFERENCES_DIR / "neobank-messaging-map.md")

    return {
        "phases": phases_text,
        "frameworks": frameworks,
        "messaging_map": messaging_map,
    }


def load_example_brief() -> str:
    """Load kast-brief.json as a few-shot example for the output schema."""
    path = EXAMPLES_DIR / "kast-brief.json"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_scraped_data(input_path: Path, competitor_slugs: list[str]) -> dict:
    """Load target scraped JSON and any competitor scraped JSONs."""
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    with open(input_path) as f:
        target = json.load(f)

    competitors = {}
    for slug in competitor_slugs:
        comp_path = OUTPUT_DIR / f"{slug}-positioning.json"
        if comp_path.exists():
            with open(comp_path) as f:
                competitors[slug] = json.load(f)
        else:
            print(f"Warning: competitor data not found at {comp_path}, skipping {slug}")

    return {"target": target, "competitors": competitors}


def truncate_page(page: dict) -> str:
    """Format a scraped page for the prompt, truncating body text."""
    lines = []
    lines.append(f"URL: {page.get('url', 'N/A')}")
    lines.append(f"Page type: {page.get('page_type', 'unknown')}")

    title = page.get("title", "")
    if title:
        lines.append(f"Title: {title}")

    meta = page.get("meta_description", "")
    if meta:
        lines.append(f"Meta description: {meta}")

    headings = page.get("headings", [])
    if headings:
        heading_strs = [f"  {h.get('tag', '?')}: {h.get('text', '')}" for h in headings[:20]]
        lines.append("Headings:\n" + "\n".join(heading_strs))

    ctas = page.get("links_text", [])
    if ctas:
        lines.append("CTAs/buttons: " + " | ".join(ctas[:15]))

    body = page.get("body_text", "")
    if body:
        truncated = body[:MAX_BODY_CHARS_PER_PAGE]
        if len(body) > MAX_BODY_CHARS_PER_PAGE:
            truncated += f"\n[...truncated, {len(body)} chars total]"
        lines.append(f"Body text:\n{truncated}")

    return "\n".join(lines)


def format_company_data(data: dict) -> str:
    """Format a company's scraped data for the prompt."""
    company = data.get("company", "Unknown")
    website = data.get("website", "N/A")
    pages = data.get("pages", [])

    sections = [f"## {company} ({website})", f"Scraped {len(pages)} pages."]
    for page in pages:
        sections.append(f"\n### {page.get('page_type', 'unknown').title()} page")
        sections.append(truncate_page(page))

    return "\n".join(sections)


def build_system_prompt(context: dict, example_brief: str) -> str:
    """Build the system prompt from reference files and schema."""
    parts = [
        "You are a positioning strategist. Your task is to analyze scraped website data "
        "for a crypto neobank and its competitors, then produce a structured positioning brief.",
        "",
        "Follow these analytical phases:",
        "",
        context["phases"],
        "",
        "---",
        "",
        "# Reference: Positioning Frameworks",
        context["frameworks"],
        "",
        "---",
        "",
        "# Reference: Neobank Messaging Map (known positioning of major players)",
        context["messaging_map"],
    ]

    if example_brief:
        parts.extend([
            "",
            "---",
            "",
            "# Output Schema (follow this structure exactly)",
            "Here is a complete example of the expected JSON output. Your output must have the same "
            "top-level keys and nested structure. All text values should be specific, evidence-based, "
            "and grounded in the scraped data.",
            "",
            "```json",
            example_brief,
            "```",
        ])

    parts.extend([
        "",
        "---",
        "",
        "# Output Rules",
        "1. Return ONLY valid JSON. No markdown fencing, no commentary before or after.",
        "2. Match the schema above exactly: company, date, website, competitors, executive_summary, "
        "positioning_elements, territory_map, white_space, messaging_framework.",
        "3. Every claim must trace to scraped data or the reference files. No invented stats.",
        "4. The competitor test: if a competitor could say the same thing, push harder.",
        "5. No AI slop: no 'in today\'s competitive landscape', no 'it\'s worth noting'.",
        "6. Be specific and direct. This goes to a CMO, not a chatbot.",
    ])

    return "\n".join(parts)


def build_user_prompt(scraped_data: dict) -> str:
    """Format all scraped data into the user prompt."""
    target = scraped_data["target"]
    competitors = scraped_data["competitors"]

    parts = [
        "Analyze the following scraped website data and produce a positioning brief JSON.",
        "",
        "# Target Company",
        format_company_data(target),
    ]

    if competitors:
        parts.append("\n# Competitors")
        for slug, comp_data in competitors.items():
            parts.append("")
            parts.append(format_company_data(comp_data))

    competitor_names = []
    for comp_data in competitors.values():
        competitor_names.append(comp_data.get("company", "Unknown"))
    if not competitor_names:
        competitor_names = ["(use reference data from the messaging map)"]

    parts.extend([
        "",
        f"# Instructions",
        f"Target company: {target.get('company', 'Unknown')}",
        f"Website: {target.get('website', 'N/A')}",
        f"Competitors to analyze against: {', '.join(competitor_names)}",
        f"Date: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "Produce the complete positioning brief JSON now.",
    ])

    return "\n".join(parts)


def build_repair_prompt(raw_response: str, error: str) -> str:
    """Prompt for retrying after JSON parse failure."""
    return (
        f"Your previous response was not valid JSON. Error: {error}\n\n"
        f"Here is what you returned:\n{raw_response[:3000]}\n\n"
        "Please return ONLY the valid JSON positioning brief. "
        "No markdown fencing, no extra text."
    )


REQUIRED_KEYS = {
    "company", "date", "competitors", "executive_summary",
    "positioning_elements", "territory_map", "white_space",
    "messaging_framework",
}

REQUIRED_FRAMEWORK_KEYS = {
    "positioning_statements", "one_liners", "value_propositions",
    "what_not_to_say", "competitive_responses",
}


def parse_and_validate(text: str) -> dict:
    """Parse JSON from response text and validate required keys."""
    # Strip markdown fencing if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove first line (```json or ```)
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    brief = json.loads(cleaned)

    missing = REQUIRED_KEYS - set(brief.keys())
    if missing:
        raise ValueError(f"Missing required keys: {missing}")

    framework = brief.get("messaging_framework", {})
    missing_fw = REQUIRED_FRAMEWORK_KEYS - set(framework.keys())
    if missing_fw:
        raise ValueError(f"Missing messaging_framework keys: {missing_fw}")

    return brief


def call_anthropic(system: str, user: str, model: str) -> str:
    """Call the Anthropic API directly."""
    try:
        from anthropic import Anthropic
    except ImportError:
        print("Error: pip install anthropic")
        sys.exit(1)

    client = Anthropic()
    print(f"Calling Anthropic API ({model})...")

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def call_openrouter(system: str, user: str, model: str) -> str:
    """Call OpenRouter API via the OpenAI SDK."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: pip install openai")
        sys.exit(1)

    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    print(f"Calling OpenRouter API ({model})...")

    response = client.chat.completions.create(
        model=model,
        max_tokens=8192,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def run_analysis(system: str, user: str, provider: str, model: str) -> dict:
    """Run the LLM call with one retry on parse failure."""
    call_fn = call_anthropic if provider == "anthropic" else call_openrouter

    for attempt in range(1 + MAX_RETRIES):
        if attempt == 0:
            raw = call_fn(system, user, model)
        else:
            print(f"Retry {attempt}: sending repair prompt...")
            repair = build_repair_prompt(raw, str(last_error))
            raw = call_fn(system, repair, model)

        try:
            return parse_and_validate(raw)
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"Parse error (attempt {attempt + 1}): {e}")

    print("Error: failed to get valid JSON after retries")
    print("Raw response (first 2000 chars):")
    print(raw[:2000])
    sys.exit(1)


def main():
    load_env()

    parser = argparse.ArgumentParser(
        description="Analyze scraped positioning data and generate a structured brief"
    )
    parser.add_argument(
        "input",
        help="Path to scraped positioning JSON (e.g. output/kast-positioning.json)",
    )
    parser.add_argument(
        "--competitors",
        nargs="*",
        default=[],
        help="Slugs of competitor scraped JSONs (e.g. revolut crypto-com)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Model to use (default: {DEFAULT_MODEL_ANTHROPIC} for Anthropic, "
        f"{DEFAULT_MODEL_OPENROUTER} for OpenRouter)",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openrouter"],
        default=None,
        help="Force a specific provider (default: auto-detect from available API keys)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for brief JSON (default: output/{slug}-brief.json)",
    )
    args = parser.parse_args()

    # Resolve provider
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_openrouter = bool(os.environ.get("OPENROUTER_API_KEY"))

    if args.provider:
        provider = args.provider
    elif has_anthropic:
        provider = "anthropic"
    elif has_openrouter:
        provider = "openrouter"
    else:
        print("Error: set ANTHROPIC_API_KEY or OPENROUTER_API_KEY")
        print("Copy .env.example to .env and fill in your key")
        sys.exit(1)

    if provider == "anthropic" and not has_anthropic:
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    if provider == "openrouter" and not has_openrouter:
        print("Error: OPENROUTER_API_KEY not set")
        sys.exit(1)

    model = args.model
    if not model:
        model = DEFAULT_MODEL_ANTHROPIC if provider == "anthropic" else DEFAULT_MODEL_OPENROUTER

    # Load everything
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_DIR / input_path

    print("Loading context files...")
    context = load_context_files()
    example_brief = load_example_brief()
    scraped_data = load_scraped_data(input_path, args.competitors)

    target_company = scraped_data["target"].get("company", "unknown")
    competitor_names = [d.get("company", s) for s, d in scraped_data["competitors"].items()]

    print(f"Target: {target_company}")
    print(f"Competitors: {', '.join(competitor_names) if competitor_names else '(from reference data)'}")
    print(f"Provider: {provider} ({model})")
    print("=" * 50)

    # Build prompts
    system_prompt = build_system_prompt(context, example_brief)
    user_prompt = build_user_prompt(scraped_data)

    # Estimate tokens (rough: 4 chars per token)
    est_tokens = (len(system_prompt) + len(user_prompt)) // 4
    print(f"Estimated input: ~{est_tokens:,} tokens")

    # Run analysis
    brief = run_analysis(system_prompt, user_prompt, provider, model)

    # Ensure metadata is set
    brief.setdefault("company", target_company)
    brief.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
    brief.setdefault("website", scraped_data["target"].get("website", ""))
    if not brief.get("competitors") and competitor_names:
        brief["competitors"] = competitor_names

    # Save output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(target_company)
    output_path = Path(args.output) if args.output else OUTPUT_DIR / f"{slug}-brief.json"

    with open(output_path, "w") as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)

    print("=" * 50)
    print(f"Brief saved to: {output_path}")
    print(f"\nNext: python scripts/render_positioning.py {output_path}")


if __name__ == "__main__":
    main()
