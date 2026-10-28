"""Screenshots of the demo page for the submission: hackathon/screenshots/*.png.

Serves hackathon/demo/site on a local port and captures it at 1440x900 with Playwright:

    uv run --group e2e python hackathon/demo/screenshots.py

Nothing leaves the machine: the page loads only its own files.
"""

from __future__ import annotations

import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "hackathon" / "demo" / "site"
OUT = ROOT / "hackathon" / "screenshots"


def shot(page: Page, name: str, selector: str, *, offset: int = 0, height: int = 900) -> None:
    page.locator(selector).first.scroll_into_view_if_needed()
    page.evaluate(
        "([sel, off]) => window.scrollTo(0, document.querySelector(sel).getBoundingClientRect().top"
        " + window.scrollY - 16 + off)",
        [selector, offset],
    )
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / name), clip={"x": 0, "y": 0, "width": 1440, "height": height})
    print(f"wrote {(OUT / name).relative_to(ROOT)}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    try:
        with sync_playwright() as p:
            # The installed Chrome, as the dashboard's browser test uses (pyproject.toml, e2e).
            browser = p.chromium.launch(channel="chrome")
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(url)
            page.wait_for_selector("#result-cards .card")
            page.screenshot(path=str(OUT / "1-results.png"))
            print(f"wrote {(OUT / '1-results.png').relative_to(ROOT)}")
            shot(page, "2-ladder.png", "#ladder")
            page.click("#show-escalation")
            page.click("#show-all")
            shot(page, "3-escalation.png", ".ev.escalation", offset=-420)
            shot(page, "4-reviews-and-steps.png", "#reviews")
            browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
