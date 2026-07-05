"""Render a local HTML file to PDF using headless Chromium (Playwright).
Waits for Mermaid diagrams to render; adds 1-inch margins and a bottom-right
page number, per the university formatting guidelines.
Usage: python scripts/html_to_pdf.py <input.html> <output.pdf> [landscape]"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

src = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
landscape = len(sys.argv) > 3 and sys.argv[3] == "landscape"
out.parent.mkdir(parents=True, exist_ok=True)

FOOTER = ('<div style="width:100%;font-family:Times New Roman,serif;font-size:9px;'
          'padding:0 18mm 0 0;text-align:right;color:#333;">'
          '<span class="pageNumber"></span></div>')
EMPTY = '<div></div>'

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto(src.as_uri(), wait_until="networkidle")
    n = page.eval_on_selector_all("pre.mermaid,.mermaid", "els => els.length")
    if n:
        try:
            page.wait_for_function(
                "document.querySelectorAll('.mermaid svg').length >= 1",
                timeout=45000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
    if landscape:
        # full-bleed slide decks: no margins, no page-number footer
        page.pdf(path=str(out), format="A4", landscape=True,
                 print_background=True,
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    else:
        # report: 1-inch margins + bottom-right page number (guideline format)
        page.pdf(path=str(out), format="A4", landscape=False,
                 print_background=True,
                 display_header_footer=True,
                 header_template=EMPTY, footer_template=FOOTER,
                 margin={"top": "25.4mm", "bottom": "25.4mm",
                         "left": "25.4mm", "right": "25.4mm"})
    b.close()
print("wrote", out)
