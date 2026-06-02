from sota.model.gamedata import load_game_data

def test_loads_real_data():
    gd = load_game_data()
    assert len(gd.artifacts) == 248
    assert len(gd.tablets) == 54
    assert len(gd.combos) == 19
    assert gd.artifacts["fire_bolt"]["max_level"] == 2  # level 1 + 1 (oracle-verified)
    assert gd.tablets["peace"]["effects"][0]["type"] == "level_add"
    assert gd.combos["yinggalbul"]["thresholds"][0]["count"] == 2

def test_lookup_missing_returns_none():
    gd = load_game_data()
    assert gd.artifacts.get("nope") is None
