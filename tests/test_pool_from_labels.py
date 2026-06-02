from sota.model.gamedata import load_game_data
from sota.recognize.pool_from_labels import pool_from_labels

GD = load_game_data()

def test_builds_pool_and_flags_low_confidence():
    labels = [("peace", 0.99), ("fire_bolt", 0.95), ("empty", 0.80),
              ("ohia_lehua", 0.40), ("not_a_key", 0.99), ("peace", 0.90)]
    pool, low = pool_from_labels(labels, GD, min_conf=0.5)
    assert sorted(pool.tablets) == ["peace", "peace"]
    assert pool.artifacts == ["fire_bolt"]
    assert ("ohia_lehua", 0.40) in low
