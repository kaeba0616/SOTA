import pathlib
from PIL import Image
from sota.model.layout import Layout, TabletPlacement, ArtifactPlacement
from sota.model.gamedata import load_game_data
from sota.render.grid_image import render_layout

GD = load_game_data()
ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_render_returns_image_of_expected_size():
    lay = Layout(slot_count=12,
                 tablets=[TabletPlacement("peace", 0, 1, 0)],
                 artifacts=[ArtifactPlacement("fire_bolt", 0, 0),
                            ArtifactPlacement("ohia_lehua", 0, 2)])
    img = render_layout(lay, "yinggalbul", GD, ROOT, cell=48)
    assert isinstance(img, Image.Image)
    assert img.width == 6 * 48
    assert img.height >= 2 * 48
    assert img.mode in ("RGB", "RGBA")

def test_render_saves_nonempty_png(tmp_path):
    lay = Layout(slot_count=6, tablets=[], artifacts=[ArtifactPlacement("fire_bolt", 0, 0)])
    img = render_layout(lay, "yinggalbul", GD, ROOT, cell=48)
    out = tmp_path / "layout.png"
    img.save(out)
    assert out.exists() and out.stat().st_size > 100
