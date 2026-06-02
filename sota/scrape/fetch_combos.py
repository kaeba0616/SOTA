import json, pathlib
from playwright.sync_api import sync_playwright
from sota.scrape import fiber_js

URL = "https://www.sephiria.wiki/combo"
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "combos.json"
EXPECTED = 19

def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(800)
        combos = page.evaluate(fiber_js.COMBOS)
        browser.close()
    if len(combos) != EXPECTED:
        raise RuntimeError(f"expected {EXPECTED} combos, got {len(combos)}")
    norm = [{
        "key": c["key"], "label": c["label"],
        "min_count": c["minCount"], "max_count": c["maxCount"],
        "thresholds": [{"count": e["count"], "effect": e["effect"]} for e in c["effects"]],
    } for c in combos]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(norm, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(norm)} combos -> {OUT}")

if __name__ == "__main__":
    main()
