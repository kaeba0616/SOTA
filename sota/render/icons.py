import json, functools, pathlib

@functools.lru_cache(maxsize=8)
def _idmap(root_str):
    p = pathlib.Path(root_str) / "sota" / "data" / "idmap.json"
    return json.loads(p.read_text(encoding="utf-8"))["map"]

def icon_path(kind, key, root):
    """Absolute path to an item's image, or None. Artifacts resolve through idmap
    (key -> filename) then glob the real extension; tablets are assets/tablets/{key}.png."""
    root = pathlib.Path(root)
    if kind == "tablet":
        p = root / "assets" / "tablets" / f"{key}.png"
        return p if p.exists() else None
    filename = _idmap(str(root)).get(key)
    if filename is None:
        return None
    matches = sorted((root / "assets" / "artifacts").glob(f"{filename}.*"))
    return matches[0] if matches else None
