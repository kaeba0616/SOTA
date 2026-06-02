from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement, ArtifactPlacement
from sota.model.gamedata import load_game_data
from sota.evaluate.score import score_layout, combo_stages

GD = load_game_data()

def test_combo_stages_counts_thresholds_reached():
    combo = GD.combos["yinggalbul"]
    assert combo_stages(combo, 0) == 0
    assert combo_stages(combo, 3) == 1
    assert combo_stages(combo, 6) == 3
    assert combo_stages(combo, 99) == 5

def test_score_rewards_levels_and_stages():
    lay = Layout(slot_count=12,
                 tablets=[TabletPlacement("peace", 1, 1, 0)],
                 artifacts=[ArtifactPlacement("fire_bolt", 1, 0),
                            ArtifactPlacement("ohia_lehua", 1, 2)])
    res = score_layout(lay, "yinggalbul", GD)
    assert res.stages == 1
    assert res.level_sum >= 2
    assert res.score == 1000 * res.stages + res.level_sum
    assert sorted(res.target_keys) == ["fire_bolt", "ohia_lehua"]

def test_non_target_artifacts_ignored_in_level_sum():
    lay = Layout(slot_count=12, tablets=[],
                 artifacts=[ArtifactPlacement("fire_bolt", 0, 0),
                            ArtifactPlacement("blessing", 0, 1)])
    res = score_layout(lay, "yinggalbul", GD)
    assert res.target_keys == ["fire_bolt"]
    assert res.stages == 0
