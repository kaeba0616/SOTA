import pathlib
from sota.recognize.dataset import build_canonical_dataset

ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_builds_one_image_per_item(tmp_path):
    counts = build_canonical_dataset(ROOT, tmp_path)
    assert counts["tablets"] == 54
    assert counts["artifacts"] == 248
    assert counts["empty"] >= 1
    tab_stems = {p.stem for p in (tmp_path / "tablets").iterdir()}
    assert "unity" in tab_stems and "fusion" not in tab_stems
    art_stems = {p.stem for p in (tmp_path / "artifacts").iterdir()}
    assert "fire_bolt" in art_stems
    assert len(art_stems) == 248
