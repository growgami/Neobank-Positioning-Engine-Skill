"""
Positioning Brief PDF Renderer

Usage:
    python scripts/render_positioning.py "output/kast-brief.json"

Takes a structured positioning brief JSON and renders it as a styled PDF.
The JSON should be produced by the agent during Phase 5 of the positioning workflow.

Expected JSON structure:
{
    "company": "KAST",
    "date": "2026-02-17",
    "competitors": ["Revolut", "Crypto.com", "Wirex"],
    "executive_summary": "...",
    "positioning_elements": { ... },
    "territory_map": { ... },
    "white_space": [ ... ],
    "messaging_framework": {
        "positioning_statements": [...],
        "one_liners": [...],
        "value_propositions": [...],
        "audience_messaging": [...],
        "what_not_to_say": [...],
        "competitive_responses": [...]
    }
}

Requires: pip install weasyprint
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output"


def escape_html(text: str) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_html(brief: dict) -> str:
    company = escape_html(brief.get("company", "Unknown"))
    date = brief.get("date", datetime.now().strftime("%Y-%m-%d"))
    competitors = brief.get("competitors", [])
    exec_summary = escape_html(brief.get("executive_summary", ""))
    comp_list = ", ".join(escape_html(c) for c in competitors) if competitors else "N/A"

    # Positioning elements
    elements_html = ""
    for name, elements in brief.get("positioning_elements", {}).items():
        name_escaped = escape_html(name)
        rows = ""
        for key, value in elements.items():
            key_label = escape_html(key.replace("_", " ").title())
            val_escaped = escape_html(str(value))
            rows += f'<tr><td class="label">{key_label}</td><td>{val_escaped}</td></tr>'
        elements_html += f'<div class="company-card"><h3>{name_escaped}</h3><table class="elements-table">{rows}</table></div>'

    # White space
    white_space_html = ""
    for item in brief.get("white_space", []):
        if isinstance(item, dict):
            territory = escape_html(item.get("territory", ""))
            rationale = escape_html(item.get("rationale", ""))
            white_space_html += f'<div class="white-space-item"><strong>{territory}</strong><p>{rationale}</p></div>'
        else:
            white_space_html += f'<div class="white-space-item"><p>{escape_html(str(item))}</p></div>'

    framework = brief.get("messaging_framework", {})

    # Positioning statements
    pos_statements_html = ""
    for i, stmt in enumerate(framework.get("positioning_statements", []), 1):
        if isinstance(stmt, dict):
            text = escape_html(stmt.get("text", str(stmt)))
            angle = escape_html(stmt.get("angle", ""))
            angle_div = f'<div class="pos-angle">{angle}</div>' if angle else ""
            pos_statements_html += f'<div class="pos-statement"><div class="pos-number">Option {i}</div>{angle_div}<div class="pos-text">{text}</div></div>'
        else:
            pos_statements_html += f'<div class="pos-statement"><div class="pos-number">Option {i}</div><div class="pos-text">{escape_html(str(stmt))}</div></div>'

    # One-liners
    one_liners_html = "".join(
        f'<div class="one-liner">{escape_html(str(liner))}</div>'
        for liner in framework.get("one_liners", [])
    )

    # Value propositions
    vp_html = ""
    for vp in framework.get("value_propositions", []):
        if isinstance(vp, dict):
            headline = escape_html(vp.get("headline", ""))
            support = escape_html(vp.get("supporting", ""))
            proof = escape_html(vp.get("proof_point", ""))
            vp_html += f'<div class="vp-card"><h4>{headline}</h4><p>{support}</p><div class="proof">{proof}</div></div>'

    # What not to say
    wnts_html = ""
    for item in framework.get("what_not_to_say", []):
        if isinstance(item, dict):
            phrase = escape_html(item.get("phrase", ""))
            reason = escape_html(item.get("reason", ""))
            wnts_html += f'<div class="wnts-item"><span class="wnts-phrase">{phrase}</span><span class="wnts-reason">{reason}</span></div>'

    # Competitive responses
    cr_html = ""
    for resp in framework.get("competitive_responses", []):
        if isinstance(resp, dict):
            competitor = escape_html(resp.get("competitor", ""))
            strength = escape_html(resp.get("their_strength", ""))
            weakness = escape_html(resp.get("their_weakness", ""))
            counter = escape_html(resp.get("our_counter", ""))
            cr_html += f"""<div class="cr-card"><h4>vs. {competitor}</h4>
                <div class="cr-row"><span class="cr-label">Their strength:</span> {strength}</div>
                <div class="cr-row"><span class="cr-label">Their weakness:</span> {weakness}</div>
                <div class="cr-row"><span class="cr-label">Our counter:</span> {counter}</div></div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ size: A4; margin: 20mm 18mm; }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 10pt; line-height: 1.5; color: #1a1a1a; background: #fff; }}
    .cover {{ height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 40px; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); color: #fff; page-break-after: always; }}
    .cover h1 {{ font-size: 28pt; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 12px; }}
    .cover .subtitle {{ font-size: 13pt; color: #999; margin-bottom: 40px; }}
    .cover .meta {{ font-size: 9pt; color: #666; }}
    .cover .meta span {{ display: block; margin-bottom: 4px; }}
    .cover .accent {{ width: 60px; height: 3px; background: #ff6b35; margin-bottom: 24px; }}
    h2 {{ font-size: 16pt; font-weight: 700; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #0a0a0a; }}
    h3 {{ font-size: 12pt; font-weight: 600; margin: 16px 0 8px 0; }}
    h4 {{ font-size: 10pt; font-weight: 600; margin-bottom: 4px; }}
    p {{ margin-bottom: 8px; }}
    .exec-summary {{ background: #f8f8f8; padding: 16px 20px; border-left: 3px solid #ff6b35; margin: 16px 0; font-size: 10.5pt; }}
    .company-card {{ border: 1px solid #e0e0e0; border-radius: 4px; padding: 12px 16px; margin: 12px 0; }}
    .elements-table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
    .elements-table td {{ padding: 4px 8px; border-bottom: 1px solid #f0f0f0; vertical-align: top; }}
    .elements-table .label {{ font-weight: 600; width: 140px; color: #555; }}
    .white-space-item {{ background: #f0f7f0; padding: 10px 14px; margin: 8px 0; border-left: 3px solid #2d8f2d; border-radius: 2px; }}
    .white-space-item strong {{ display: block; margin-bottom: 4px; }}
    .white-space-item p {{ font-size: 9.5pt; color: #333; }}
    .pos-statement {{ background: #fafafa; padding: 14px 18px; margin: 10px 0; border: 1px solid #e0e0e0; border-radius: 4px; }}
    .pos-number {{ font-size: 8pt; font-weight: 700; color: #ff6b35; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }}
    .pos-angle {{ font-size: 9pt; color: #666; font-style: italic; margin-bottom: 6px; }}
    .pos-text {{ font-size: 10.5pt; line-height: 1.6; }}
    .one-liner {{ font-size: 14pt; font-weight: 700; padding: 8px 0; border-bottom: 1px solid #eee; }}
    .vp-card {{ display: inline-block; width: 30%; vertical-align: top; padding: 10px; margin: 5px 1%; border: 1px solid #e0e0e0; border-radius: 4px; }}
    .vp-card h4 {{ color: #ff6b35; }}
    .vp-card .proof {{ font-size: 8.5pt; color: #666; font-style: italic; margin-top: 6px; }}
    .wnts-item {{ padding: 6px 0; border-bottom: 1px solid #f0f0f0; display: flex; gap: 12px; }}
    .wnts-phrase {{ font-weight: 600; color: #c0392b; min-width: 200px; text-decoration: line-through; }}
    .wnts-reason {{ font-size: 9pt; color: #555; }}
    .cr-card {{ border: 1px solid #e0e0e0; border-radius: 4px; padding: 12px 16px; margin: 10px 0; }}
    .cr-card h4 {{ margin-bottom: 8px; }}
    .cr-row {{ font-size: 9pt; margin: 3px 0; }}
    .cr-label {{ font-weight: 600; color: #555; }}
    .footer {{ margin-top: 40px; padding-top: 12px; border-top: 1px solid #ddd; font-size: 8pt; color: #999; text-align: center; }}
    .page-break {{ page-break-before: always; }}
</style>
</head>
<body>
<div class="cover">
    <div class="accent"></div>
    <h1>Positioning Brief</h1>
    <div class="subtitle">{company} vs. {comp_list}</div>
    <div class="meta">
        <span>Neobank Positioning Engine</span>
        <span>{date}</span>
    </div>
</div>

<h2>Executive Summary</h2>
<div class="exec-summary">{exec_summary}</div>

<h2>Positioning Elements</h2>
<p>Extracted from website copy, app store descriptions, and social presence.</p>
{elements_html}

<div class="page-break"></div>

<h2>White Space</h2>
<p>Positioning territories that are unclaimed or weakly held.</p>
{white_space_html}

<h2>Messaging Framework</h2>

<h3>Positioning Statements</h3>
{pos_statements_html}

<h3>One-Liner Options</h3>
{one_liners_html}

<div class="page-break"></div>

<h3>Value Propositions</h3>
<div>{vp_html}</div>

<h3>What NOT to Say</h3>
{wnts_html}

<div class="page-break"></div>

<h3>Competitive Response</h3>
{cr_html}

<div class="footer">
    Generated by Neobank Positioning Engine
</div>
</body>
</html>"""


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/render_positioning.py "output/brief.json"')
        sys.exit(1)

    brief_path = Path(sys.argv[1])
    if not brief_path.is_absolute():
        brief_path = PROJECT_DIR / brief_path

    with open(brief_path) as f:
        brief = json.load(f)

    html = render_html(brief)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = brief.get("company", "unknown").lower().replace(" ", "-")
    html_path = OUTPUT_DIR / f"{slug}-positioning-brief.html"

    with open(html_path, "w") as f:
        f.write(html)

    print(f"HTML: {html_path}")

    # Try WeasyPrint for PDF
    try:
        from weasyprint import HTML
        pdf_path = html_path.with_suffix(".pdf")
        HTML(string=html).write_pdf(str(pdf_path))
        print(f"PDF: {pdf_path}")
    except ImportError:
        print("Install weasyprint for PDF output: pip install weasyprint")
        print("Or open the HTML file in a browser and print to PDF.")


if __name__ == "__main__":
    main()
