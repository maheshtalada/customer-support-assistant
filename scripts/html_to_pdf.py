"""Render a local HTML file to PDF using headless Chromium (Playwright).
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
    page.goto(src.as_uri())
    page.wait_for_timeout(1200)
    page.pdf(path=str(out), format="A4", landscape=landscape,
             print_background=True,
             margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    b.close()
print("wrote", out)
