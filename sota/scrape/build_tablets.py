import json, pathlib
from sota.scrape.tablet_normalize import normalize_tablet
from sota.scrape.reconcile import reconcile, STALE_TABLET_KEYS
from sota.scrape.authored_tablets import AUTHORED

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEGACY = ROOT / "tablet.json"
SLABS = ROOT / "sota" / "data" / "slabs_raw.json"
OUT = ROOT / "sota" / "data" / "tablets.json"

def main() -> None:
    legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
    slab_keys = {s["id"] for s in json.loads(SLABS.read_text(encoding="utf-8"))}
    tablets = [normalize_tablet(t) for t in legacy]
    tablets = [t for t in tablets if t["key"] not in STALE_TABLET_KEYS]
    have = {t["key"] for t in tablets}
    rep = reconcile(have, slab_keys)
    authored_keys = {a["key"] for a in AUTHORED}
    if authored_keys != rep["missing"]:
        raise RuntimeError(f"authored {sorted(authored_keys)} != missing {sorted(rep['missing'])} — game changed?")
    next_id = max(int(t["id"].split("_")[1]) for t in tablets) + 1
    for a in AUTHORED:
        tablets.append({"id": f"tb_{next_id:03d}",
                        "key": a["key"], "name": a["name"],
                        "image": f"assets/tablets/{a['key']}.png",
                        "rotatable": a["rotatable"], "size": a["size"],
                        "rarity": a["rarity"], "restriction": a["restriction"],
                        "effects": a["effects"]})
        next_id += 1
    OUT.write_text(json.dumps(tablets, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(tablets)} tablets; authored {sorted(authored_keys)}; stale {sorted(STALE_TABLET_KEYS)}")

if __name__ == "__main__":
    main()
