import json, pathlib, requests

BASE = pathlib.Path(__file__).resolve().parents[1]
ROOT = BASE.parent
DEST = ROOT / "assets" / "tablets"
URL_TMPL = "https://img.sephiria.wiki/slabs/{key}.png"

def _try_urls(key: str) -> bytes | None:
    """Try the canonical key URL, then a hyphenated variant. Return content or None."""
    candidates = [URL_TMPL.format(key=key)]
    hyphen = key.replace("_", "-")
    if hyphen != key:
        candidates.append(URL_TMPL.format(key=hyphen))
    for url in candidates:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.content
    return None

def main() -> None:
    tablets = json.loads((BASE / "data" / "tablets.json").read_text(encoding="utf-8"))
    DEST.mkdir(parents=True, exist_ok=True)
    missing = [t["key"] for t in tablets if not (DEST / f"{t['key']}.png").exists()]
    failed = []
    for key in missing:
        content = _try_urls(key)
        if content is None:
            print(f"WARNING: all URL variants 404 for {key} — skipping")
            failed.append(key)
            continue
        (DEST / f"{key}.png").write_bytes(content)
        print(f"downloaded {key}.png")
    downloaded = len(missing) - len(failed)
    print(f"done: {downloaded} tablet images")
    if failed:
        print(f"CONCERN: {len(failed)} key(s) returned 404 and were not downloaded: {failed}")

if __name__ == "__main__":
    main()
