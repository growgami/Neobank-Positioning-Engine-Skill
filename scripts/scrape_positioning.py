"""
Neobank Positioning Scraper

Usage:
    python scripts/scrape_positioning.py "Company Name" "https://website.com"

Scrapes a company's website to extract positioning elements:
headlines, value props, CTAs, proof points, feature claims,
and brand voice signals.

Outputs structured JSON to output/{slug}-positioning.json

Requires: pip install playwright && playwright install chromium
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Install playwright: pip install playwright && playwright install chromium")
    sys.exit(1)


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def scrape_page(page, url: str, page_type: str) -> dict:
    """Scrape a single page for positioning content."""
    result = {
        "url": url,
        "page_type": page_type,
        "title": "",
        "meta_description": "",
        "headings": [],
        "body_text": "",
        "links_text": [],
        "error": None,
    }
    try:
        response = await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        if response and response.status >= 400:
            result["error"] = f"HTTP {response.status}"
            return result

        await asyncio.sleep(2)

        # Extract structured content
        result["title"] = await page.title()

        # Meta description
        meta = await page.query_selector('meta[name="description"]')
        if meta:
            result["meta_description"] = await meta.get_attribute("content") or ""

        # All headings
        headings = await page.evaluate("""
            () => Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
                tag: h.tagName,
                text: h.innerText.trim()
            })).filter(h => h.text.length > 0 && h.text.length < 200)
        """)
        result["headings"] = headings[:30]

        # Button/CTA text
        ctas = await page.evaluate("""
            () => Array.from(document.querySelectorAll('button, a[class*="btn"], a[class*="cta"], [role="button"]'))
                .map(el => el.innerText.trim())
                .filter(t => t.length > 0 && t.length < 60)
                .filter((v, i, a) => a.indexOf(v) === i)
        """)
        result["links_text"] = ctas[:20]

        # Visible body text (first 15000 chars)
        body = await page.evaluate("""
            () => {
                const walker = document.createTreeWalker(
                    document.body, NodeFilter.SHOW_TEXT, null
                );
                let text = [];
                let node;
                while (node = walker.nextNode()) {
                    const t = node.textContent.trim();
                    if (t.length > 10 && t.length < 500) text.push(t);
                }
                return text.join('\\n');
            }
        """)
        result["body_text"] = body[:15000]

    except Exception as e:
        result["error"] = str(e)

    return result


async def main():
    if len(sys.argv) < 3:
        print('Usage: python scripts/scrape_positioning.py "Company" "https://website.com"')
        sys.exit(1)

    company_name = sys.argv[1]
    website_url = sys.argv[2].rstrip("/")
    slug = slugify(company_name)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Scraping positioning data for: {company_name}")
    print(f"Website: {website_url}")
    print("=" * 50)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        data = {
            "company": company_name,
            "website": website_url,
            "scraped_at": datetime.now().isoformat(),
            "pages": [],
        }

        # Pages to scrape
        pages_to_try = [
            (website_url, "homepage"),
            (f"{website_url}/about", "about"),
            (f"{website_url}/about-us", "about"),
            (f"{website_url}/features", "features"),
            (f"{website_url}/pricing", "pricing"),
            (f"{website_url}/products", "products"),
            (f"{website_url}/why-us", "why"),
        ]

        seen_types = set()
        for url, page_type in pages_to_try:
            # Skip duplicate page types that already returned content
            if page_type in seen_types and page_type != "homepage":
                continue

            print(f"\n[Scraping] {page_type}: {url}")
            page_data = await scrape_page(page, url, page_type)

            if page_data["error"]:
                print(f"  Skipped: {page_data['error']}")
                continue

            body_len = len(page_data.get("body_text", ""))
            if body_len < 200 and page_type != "homepage":
                print(f"  Thin content ({body_len} chars), skipping")
                continue

            data["pages"].append(page_data)
            seen_types.add(page_type)
            print(f"  Got {body_len} chars, {len(page_data['headings'])} headings, {len(page_data['links_text'])} CTAs")

        await browser.close()

    # Save output
    output_path = OUTPUT_DIR / f"{slug}-positioning.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"\n{'=' * 50}")
    print(f"Saved to: {output_path}")
    print(f"Pages scraped: {len(data['pages'])}")
    print(f"\nNext: read this file and run the positioning extraction (Phase 2 in SKILL.md)")


if __name__ == "__main__":
    asyncio.run(main())
