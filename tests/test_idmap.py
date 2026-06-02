from sota.scrape.idmap import match_images

def test_exact_canon_and_digit_suffix():
    keys = ["fire_bolt", "lightning_boomerang", "calges"]
    files = ["fire_bolt", "lightningboomerang", "calges_2"]
    m = match_images(keys, files)
    assert m["map"]["fire_bolt"] == "fire_bolt"
    assert m["map"]["lightning_boomerang"] == "lightningboomerang"  # collapsed-alnum match
    assert m["map"]["calges"] == "calges_2"                          # numeric-suffix match

def test_longer_key_does_not_collide_with_shorter_sibling():
    m = match_images(["thunder_judgment", "thunder"], ["thunder", "green_tooth"])
    assert m["map"]["thunder"] == "thunder"
    assert "thunder_judgment" in m["missing"]           # must NOT map to thunder
    assert m["map"].get("thunder_judgment") != "thunder"
