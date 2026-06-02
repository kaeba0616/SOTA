import re
import json, os, pathlib


def _canon(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def match_images(keys: list[str], files: list[str]) -> dict:
    """Map artifact key -> local image filename.

    Exact filename, then collapsed-alnum equality, then a file that is the key
    plus a numeric disambiguation suffix (e.g. 'calges' -> 'calges_2'). Anything
    else goes to `missing` so the image can be fetched by its real key.
    """
    by_canon = {}
    for f in files:
        by_canon.setdefault(_canon(f), f)
    mapping, missing = {}, []
    fileset = set(files)
    for k in keys:
        ck = _canon(k)
        if k in fileset:
            mapping[k] = k
        elif ck in by_canon:
            mapping[k] = by_canon[ck]
        else:
            hit = next((f for cf, f in by_canon.items()
                        if cf.startswith(ck) and cf[len(ck):].isdigit()), None)
            if hit:
                mapping[k] = hit
            else:
                missing.append(k)
    return {"map": mapping, "missing": missing}


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
