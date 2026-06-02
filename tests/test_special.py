from sota.model.gamedata import load_game_data
from sota.evaluate.special import is_special

GD = load_game_data()

def test_known_special_flagged():
    assert is_special(GD.artifacts["calges"])
    assert is_special(GD.artifacts["black_scales"])

def test_plain_artifact_not_flagged():
    assert not is_special(GD.artifacts["fire_bolt"])
