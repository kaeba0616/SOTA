from sota.model.gamedata import load_game_data
from sota.recognize.keymap import label_to_item

GD = load_game_data()

def test_maps_tablet_artifact_empty_unknown():
    assert label_to_item("peace", GD) == ("tablet", "peace")
    assert label_to_item("fire_bolt", GD) == ("artifact", "fire_bolt")
    assert label_to_item("empty", GD) is None
    assert label_to_item("not_a_real_key", GD) is None
