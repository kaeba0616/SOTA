from sota.scrape.reconcile import reconcile, MISSING_TABLET_KEYS, STALE_TABLET_KEYS

def test_reconcile_classifies_keys():
    tablet_keys = {"approximation", "advent", "encouragement"}
    slab_keys = {"approximation", "advent", "courage"}
    rep = reconcile(tablet_keys, slab_keys)
    assert rep["matched"] == {"approximation", "advent"}
    assert "courage" in rep["missing"]
    assert "encouragement" in rep["stale"]

def test_full_missing_set_has_five():
    assert len(MISSING_TABLET_KEYS) == 5
    assert "peace" in MISSING_TABLET_KEYS
