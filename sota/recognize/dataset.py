import json, pathlib, shutil

def _idmap(root):
    return json.loads((root / "sota" / "data" / "idmap.json").read_text(encoding="utf-8"))["map"]

def _load(root, name):
    return json.loads((root / "sota" / "data" / name).read_text(encoding="utf-8"))

def build_canonical_dataset(root, dest):
    """Copy one image per item named by canonical key into dest/{tablets,artifacts,empty}.
    Tablets: assets/tablets/{key}.png. Artifacts: idmap key->filename, real extension.
    Returns per-class counts."""
    root, dest = pathlib.Path(root), pathlib.Path(dest)
    idmap = _idmap(root)
    counts = {"tablets": 0, "artifacts": 0, "empty": 0}

    tdir = dest / "tablets"; tdir.mkdir(parents=True, exist_ok=True)
    for t in _load(root, "tablets.json"):
        src = root / "assets" / "tablets" / f"{t['key']}.png"
        if src.exists():
            shutil.copy(src, tdir / f"{t['key']}.png")
            counts["tablets"] += 1

    adir = dest / "artifacts"; adir.mkdir(parents=True, exist_ok=True)
    for a in _load(root, "artifacts.json"):
        filename = idmap.get(a["key"])
        if filename is None:
            continue
        matches = sorted((root / "assets" / "artifacts").glob(f"{filename}.*"))
        if matches:
            shutil.copy(matches[0], adir / f"{a['key']}{matches[0].suffix}")
            counts["artifacts"] += 1

    edir = dest / "empty"; edir.mkdir(parents=True, exist_ok=True)
    empty_src = root / "CNN" / "slot_empty.png"
    if empty_src.exists():
        shutil.copy(empty_src, edir / "empty.png")
        counts["empty"] += 1
    return counts
