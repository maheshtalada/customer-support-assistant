"""Capture UC-02 offer-recommendation screenshots. Assumes a Streamlit server
is running on the given port. Run: python scripts/capture_offers.py <port>"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "8600"
URL = f"http://localhost:{PORT}"
OUT = Path("docs/screenshots")


def wait(page, ms=2600):
    page.wait_for_timeout(ms)


def fill(page, label, value):
    page.get_by_role("textbox", name=label).first.fill(value)


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1360, "height": 1000})
        page.goto(URL)
        wait(page, 4000)
        page.get_by_role("button", name="Get started").first.click()
        wait(page)
        # Ethan (GOLD) — has loyalty + data offers
        fill(page, "Email", "ethan.walker@example.com")
        fill(page, "Password", "teleco123")
        page.get_by_role("button", name="Sign in").first.click()
        wait(page)
        fill(page, "Last 4 digits", "4821")
        page.get_by_role("button", name="Verify").first.click()
        wait(page, 3500)

        def say(text, ms=3500):
            box = page.get_by_placeholder("Ask about your bill, a charge, or offers…")
            box.fill(text)
            box.press("Enter")
            wait(page, ms)

        say("do you have any offers for me")
        page.screenshot(path=str(OUT / "09-offer-recommendation.png"))
        print("captured 09-offer-recommendation")

        say("yes please apply it")
        page.screenshot(path=str(OUT / "10-offer-applied.png"))
        print("captured 10-offer-applied")

        b.close()
        print("done")


if __name__ == "__main__":
    main()
