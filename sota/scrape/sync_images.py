import json, pathlib, requests

BASE = pathlib.Path(__file__).resolve().parents[1]
ROOT = BASE.parent
DEST = ROOT / "assets" / "artifacts"
URL_TMPL = "https://img.sephiria.wiki/artifacts/{key}.png"

def main() -> None:
    missing = json.loads((BASE / "data" / "idmap.json").read_text(encoding="utf-8"))["missing"]
    arts = {a["key"]: a for a in json.loads((BASE / "data" / "artifacts.json").read_text(encoding="utf-8"))}
    DEST.mkdir(parents=True, exist_ok=True)
    for key in missing:
        url = arts.get(key, {}).get("image") or URL_TMPL.format(key=key)
        ext = ".webp" if url.endswith(".webp") else ".png"
        out = DEST / f"{key}{ext}"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        out.write_bytes(r.content)
        print(f"downloaded {out.name}")
    print(f"done: {len(missing)} images")

if __name__ == "__main__":
    main()
