import re
import difflib


def _canon(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def match_images(keys: list[str], files: list[str]) -> dict:
    """Map artifact key -> local image filename. Exact, then collapsed-alnum, then prefix, then fuzzy."""
    by_canon = {}
    for f in files:
        by_canon.setdefault(_canon(f), f)
    canon_list = list(by_canon.keys())
    mapping, missing = {}, []
    fileset = set(files)
    for k in keys:
        if k in fileset:
            mapping[k] = k
        elif _canon(k) in by_canon:
            mapping[k] = by_canon[_canon(k)]
        else:
            ck = _canon(k)
            # prefix match
            hit = next((f for cf, f in by_canon.items() if cf.startswith(ck) or ck.startswith(cf)), None)
            if hit:
                mapping[k] = hit
            else:
                # fuzzy match via SequenceMatcher
                matches = difflib.get_close_matches(ck, canon_list, n=1, cutoff=0.7)
                if matches:
                    mapping[k] = by_canon[matches[0]]
                else:
                    missing.append(k)
    return {"map": mapping, "missing": missing}


import json, os, pathlib


def main() -> None:
    base = pathlib.Path(__file__).resolve().parents[1]
    root = base.parent
    arts = json.loads((base / "data" / "artifacts.json").read_text(encoding="utf-8"))
    files = [os.path.splitext(f)[0] for f in os.listdir(root / "assets" / "artifacts")]
    res = match_images([a["key"] for a in arts], files)
    (base / "data" / "idmap.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"mapped {len(res['map'])}, missing images: {len(res['missing'])} -> {res['missing']}")


if __name__ == "__main__":
    main()
