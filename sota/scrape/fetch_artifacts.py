import json, pathlib
from playwright.sync_api import sync_playwright
from sota.scrape import fiber_js
from sota.scrape.artifact_parse import normalize_artifact

URL = "https://www.sephiria.wiki/simulator"
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "artifacts.json"
EXPECTED = 248

def fetch_raw() -> list:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.get_by_role("tab", name="아티팩트").click()
        page.wait_for_timeout(1200)
        raw = page.evaluate(fiber_js.ARTIFACTS)
        browser.close()
    if not raw:
        raise RuntimeError("artifact extraction returned nothing — site structure changed")
    return raw

def main() -> None:
    raw = fetch_raw()
    arts = [normalize_artifact(a) for a in raw]
    if len(arts) != EXPECTED:
        raise RuntimeError(f"expected {EXPECTED} artifacts, got {len(arts)} (game patch? update EXPECTED)")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(arts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(arts)} artifacts -> {OUT}")

if __name__ == "__main__":
    main()
