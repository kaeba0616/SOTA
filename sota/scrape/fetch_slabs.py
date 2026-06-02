import json, pathlib
from playwright.sync_api import sync_playwright
from sota.scrape import fiber_js

URL = "https://www.sephiria.wiki/simulator"
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "slabs_raw.json"
EXPECTED = 54

def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.get_by_role("tab", name="석판").click()
        page.wait_for_timeout(800)
        slabs = page.evaluate(fiber_js.SLABS)
        browser.close()
    if not slabs or len(slabs) != EXPECTED:
        raise RuntimeError(f"expected {EXPECTED} slabs, got {len(slabs or [])}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(slabs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(slabs)} slabs -> {OUT}")

if __name__ == "__main__":
    main()
