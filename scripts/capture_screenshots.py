"""Auto-capture UI screenshots for the README by driving the app headlessly.
Run (from repo root, venv active):  python scripts/capture_screenshots.py
Requires: playwright (pip install playwright && python -m playwright install chromium)
and a Streamlit server already running on PORT (see the __main__ block)."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "8600"
URL = f"http://localhost:{PORT}"
OUT = Path("docs/screenshots")
OUT.mkdir(parents=True, exist_ok=True)


def wait(page, ms=2500):
    page.wait_for_timeout(ms)


def fill_by_label(page, label, value):
    page.get_by_role("textbox", name=label).first.fill(value)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 1000})
        page.goto(URL)
        wait(page, 4000)

        # 1) Welcome
        page.screenshot(path=str(OUT / "01-welcome.png"))
        print("captured 01-welcome")

        # -> login
        page.get_by_role("button", name="Get started").first.click()
        wait(page)
        page.screenshot(path=str(OUT / "02-login.png"))
        print("captured 02-login")

        # fill + sign in
        fill_by_label(page, "Email", "marcus.rivera@example.com")
        fill_by_label(page, "Password", "teleco123")
        page.get_by_role("button", name="Sign in").first.click()
        wait(page)

        # 3) identity verify
        page.screenshot(path=str(OUT / "03-verify.png"))
        print("captured 03-verify")
        fill_by_label(page, "Last 4 digits", "1100")
        page.get_by_role("button", name="Verify").first.click()
        wait(page, 3500)
        page.screenshot(path=str(OUT / "04-chat-start.png"))
        print("captured 04-chat-start")

        def say(text, wait_ms=3500):
            box = page.get_by_placeholder("Ask about your bill, a charge, or offers…")
            box.fill(text)
            box.press("Enter")
            wait(page, wait_ms)

        # billing dispute
        say("why is my bill higher this month")
        page.screenshot(path=str(OUT / "05-bill-explain.png"))
        print("captured 05-bill-explain")

        say("i never used that much data")
        page.screenshot(path=str(OUT / "06-dispute-evidence.png"))
        print("captured 06-dispute-evidence")

        # haggle -> handoff to retention
        say("that is too expensive can you do better")
        page.screenshot(path=str(OUT / "07-handoff-retention.png"))
        print("captured 07-handoff-retention")

        # accept -> resolved
        say("ok yes fine apply it")
        page.screenshot(path=str(OUT / "08-resolved.png"))
        print("captured 08-resolved")

        browser.close()
        print("\nDone ->", OUT.resolve())


if __name__ == "__main__":
    main()
