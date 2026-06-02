import json, pathlib
from sota.scrape.tablet_normalize import normalize_tablet
from sota.scrape.reconcile import reconcile, MISSING_TABLET_KEYS, STALE_TABLET_KEYS

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEGACY = ROOT / "tablet.json"
SLABS = ROOT / "sota" / "data" / "slabs_raw.json"
OUT = ROOT / "sota" / "data" / "tablets.json"

def main() -> None:
    legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
    slabs = {s["id"]: s["label"] for s in json.loads(SLABS.read_text(encoding="utf-8"))}
    tablets = [normalize_tablet(t) for t in legacy]
    tablets = [t for t in tablets if t["key"] not in STALE_TABLET_KEYS]  # drop removed
    have = {t["key"] for t in tablets}
    # add stubs for missing tablets (geometry filled manually later)
    next_id = max(int(t["id"].split("_")[1]) for t in tablets) + 1
    for key, name in MISSING_TABLET_KEYS.items():
        if key in have:
            continue
        tablets.append({
            "id": f"tb_{next_id:03d}", "key": key, "name": name,
            "image": f"assets/tablets/{key}.png",
            "rotatable": False, "size": [1, 1], "rarity": None,
            "restriction": None, "effects": [], "_TODO_geometry": True,
        })
        next_id += 1
    have = {t["key"] for t in tablets}
    rep = reconcile(have, set(slabs))
    OUT.write_text(json.dumps(tablets, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(tablets)} tablets; missing in game: {sorted(rep['missing'])}; stale dropped: {sorted(STALE_TABLET_KEYS)}")

if __name__ == "__main__":
    main()
