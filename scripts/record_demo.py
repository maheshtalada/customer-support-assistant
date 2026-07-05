"""Record an end-to-end demo video of the chatbot (Playwright screen capture).
Saves a .webm under docs/demo/ ; convert to .mp4 with ffmpeg if available.
Run: python scripts/record_demo.py <port>"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "8600"
NAME = sys.argv[2] if len(sys.argv) > 2 else "demo"          # output basename
TURN_WAIT = int(sys.argv[3]) if len(sys.argv) > 3 else 4200  # ms to wait per reply
URL = f"http://localhost:{PORT}"
OUT = Path("docs/demo")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1360, "height": 950},
                            record_video_dir=str(OUT),
                            record_video_size={"width": 1360, "height": 950})
        page = ctx.new_page()

        def pause(ms):
            page.wait_for_timeout(ms)

        def fill(label, value):
            box = page.get_by_role("textbox", name=label).first
            box.click()
            box.type(value, delay=35)

        def say(text, ms=TURN_WAIT):
            box = page.get_by_placeholder("Ask about your bill, a charge, or offers…")
            box.click()
            box.type(text, delay=30)
            pause(500)
            box.press("Enter")
            pause(ms)

        page.goto(URL)
        pause(4000)          # welcome page
        page.get_by_role("button", name="Get started").first.click()
        pause(2200)          # login
        fill("Email", "marcus.rivera@example.com")
        fill("Password", "teleco123")
        pause(800)
        page.get_by_role("button", name="Sign in").first.click()
        pause(2200)          # verify
        fill("Last 4 digits", "1100")
        pause(700)
        page.get_by_role("button", name="Verify").first.click()
        pause(3500)          # chat start

        say("why is my bill higher this month")
        say("i never used that much data")
        say("that is too expensive can you do better")   # -> handoff
        say("no that is still too much")
        say("ok yes fine apply it")                       # -> resolved
        pause(4000)

        ctx.close()          # finalizes the video file
        b.close()

    vids = sorted(OUT.glob("*.webm"))
    if vids:
        final = OUT / f"{NAME}.webm"
        vids[-1].rename(final)
        for v in OUT.glob("*.webm"):
            if v != final:
                v.unlink()
        print("saved", final)


if __name__ == "__main__":
    main()
