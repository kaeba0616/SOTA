from sota.scrape.idmap import match_images

def test_exact_and_fuzzy_and_missing():
    keys = ["fire_bolt", "lightning_boomerang", "calges", "defect_probe"]
    files = ["fire_bolt", "lightningboomerald", "calges_2", "green_tooth"]
    m = match_images(keys, files)
    assert m["map"]["fire_bolt"] == "fire_bolt"
    assert m["map"]["lightning_boomerang"] == "lightningboomerald"
    assert m["map"]["calges"] == "calges_2"
    assert "defect_probe" in m["missing"]
