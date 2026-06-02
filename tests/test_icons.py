import pathlib
from sota.render.icons import icon_path

ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_tablet_icon_resolves():
    p = icon_path("tablet", "peace", ROOT)
    assert p is not None and p.exists() and p.name == "peace.png"

def test_artifact_icon_resolves_via_idmap():
    p = icon_path("artifact", "fire_bolt", ROOT)
    assert p is not None and p.exists()

def test_unknown_key_returns_none():
    assert icon_path("artifact", "definitely_not_real", ROOT) is None
