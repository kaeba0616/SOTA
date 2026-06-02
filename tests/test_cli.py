import pathlib
from sota.model.gamedata import load_game_data
from sota.cli import run

GD = load_game_data()
ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_run_solves_and_writes_image(tmp_path):
    out = tmp_path / "build.png"
    summary = run(tablets=["peace"], artifacts=["fire_bolt", "ohia_lehua"],
                  combo="yinggalbul", slots=12, seed=7, out=str(out),
                  gamedata=GD, root=ROOT, generations=20, pop_size=24)
    assert summary["combo"] == "yinggalbul"
    assert summary["score"] >= 1000
    assert out.exists() and out.stat().st_size > 100


def test_run_rejects_unknown_keys():
    import pytest
    with pytest.raises(ValueError) as e:
        run(tablets=["nope_tablet"], artifacts=[], combo="yinggalbul",
            slots=12, seed=0, out=None, gamedata=GD, root=ROOT)
    assert "nope_tablet" in str(e.value)


def test_run_rejects_unknown_combo():
    import pytest
    with pytest.raises(ValueError) as e:
        run(tablets=[], artifacts=["fire_bolt"], combo="not_a_combo",
            slots=12, seed=0, out=None, gamedata=GD, root=ROOT)
    assert "not_a_combo" in str(e.value)


def test_main_list_combos(capsys):
    from sota.cli import main
    rc = main(["--list-combos"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "yinggalbul" in out
    assert len(out.strip().splitlines()) == 19


def test_main_full_run(tmp_path, capsys):
    from sota.cli import main
    out = tmp_path / "b.png"
    rc = main(["--combo", "yinggalbul", "--tablets", "peace",
               "--artifacts", "fire_bolt,ohia_lehua", "--slots", "12",
               "--seed", "5", "--generations", "15", "--pop-size", "20",
               "--out", str(out)])
    assert rc == 0
    assert out.exists() and out.stat().st_size > 100
    assert "score" in capsys.readouterr().out.lower()


def test_main_unknown_combo_returns_error_code(capsys):
    from sota.cli import main
    rc = main(["--combo", "bogus", "--artifacts", "fire_bolt"])
    assert rc == 2
    assert "bogus" in capsys.readouterr().err
