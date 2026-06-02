import pathlib
from sota.model.gamedata import load_game_data
from sota.cli import run_from_screenshot

GD = load_game_data()
ROOT = pathlib.Path(__file__).resolve().parents[1]

def fake_recognizer(path):
    return [("peace", 0.99), ("fire_bolt", 0.97), ("ohia_lehua", 0.96),
            ("empty", 0.9), ("ignition", 0.3)]

def test_run_from_screenshot_solves(tmp_path, capsys):
    out = tmp_path / "b.png"
    summary, low = run_from_screenshot(
        screenshot="ignored.png", combo="yinggalbul", slots=12, seed=7,
        out=str(out), gamedata=GD, root=ROOT, recognize_fn=fake_recognizer,
        min_conf=0.5, generations=15, pop_size=20)
    assert summary["combo"] == "yinggalbul"
    assert summary["score"] >= 1000
    assert ("ignition", 0.3) in low
    assert out.exists()
