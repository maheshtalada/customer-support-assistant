"""Render a local HTML file to PDF using headless Chromium (Playwright).
Waits for any Mermaid diagrams to finish rendering before printing.
Usage: python scripts/html_to_pdf.py <input.html> <output.pdf> [landscape]"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

src = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
landscape = len(sys.argv) > 3 and sys.argv[3] == "landscape"
out.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto(src.as_uri(), wait_until="networkidle")
    # If the doc uses Mermaid, wait until diagrams are rendered to SVG.
    n = page.eval_on_selector_all("pre.mermaid,.mermaid", "els => els.length")
    if n:
        try:
            page.wait_for_function(
                "document.querySelectorAll('.mermaid svg').length >= "
                + str(min(n, 1)), timeout=30000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
    page.pdf(path=str(out), format="A4", landscape=landscape,
             print_background=True,
             margin={"top": "14mm", "bottom": "14mm", "left": "0", "right": "0"})
    b.close()
print("wrote", out)
