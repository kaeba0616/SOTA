from sota.model.pool import ItemPool
from sota.model.gamedata import load_game_data
from sota.evaluate.score import score_layout
from sota.solve.ga import solve

GD = load_game_data()

def test_solve_is_deterministic_and_beats_empty_baseline():
    r1 = solve(ItemPool(tablets=["peace"], artifacts=["fire_bolt", "ohia_lehua"]),
               "yinggalbul", slot_count=12, gamedata=GD, seed=7, generations=30, pop_size=24)
    r2 = solve(ItemPool(tablets=["peace"], artifacts=["fire_bolt", "ohia_lehua"]),
               "yinggalbul", slot_count=12, gamedata=GD, seed=7, generations=30, pop_size=24)
    assert r1.score == r2.score
    assert r1.score >= 1000
    assert all(b <= a for b, a in zip(r1.history, r1.history[1:]))
    assert score_layout(r1.layout, "yinggalbul", GD).score == r1.score

def test_solve_finds_boost_placement():
    res = solve(ItemPool(tablets=["peace"], artifacts=["ohia_lehua", "ohia_lehua"]),
                "yinggalbul", slot_count=6, gamedata=GD, seed=3, generations=40, pop_size=30)
    assert res.score > 1000 + 2
