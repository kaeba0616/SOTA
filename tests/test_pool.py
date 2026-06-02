from sota.model.pool import ItemPool

def test_candidates_preserve_duplicates_and_kind():
    p = ItemPool(tablets=["peace", "peace"], artifacts=["fire_bolt"])
    assert p.candidates() == [("tablet", "peace"), ("tablet", "peace"), ("artifact", "fire_bolt")]
    assert len(p) == 3

def test_empty_pool():
    p = ItemPool(tablets=[], artifacts=[])
    assert p.candidates() == []
    assert len(p) == 0
