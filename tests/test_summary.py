from sota.model.grid import Grid
from sota.model.layout import Layout, TabletPlacement, ArtifactPlacement
from sota.model.gamedata import load_game_data
from sota.render.summary import build_summary, format_summary

GD = load_game_data()

def test_build_summary_fields():
    lay = Layout(slot_count=12,
                 tablets=[TabletPlacement("peace", 0, 1, 0)],
                 artifacts=[ArtifactPlacement("fire_bolt", 0, 0),
                            ArtifactPlacement("ohia_lehua", 0, 2)])
    s = build_summary(lay, "yinggalbul", GD)
    assert s["stages"] == 1
    assert s["score"] == 1000 * s["stages"] + s["level_sum"]
    ohia = next(t for t in s["targets"] if t["key"] == "ohia_lehua")
    assert ohia["cell"] == [0, 2] and ohia["level"] == 3
    fire = next(t for t in s["targets"] if t["key"] == "fire_bolt")
    assert fire["level"] == 2  # boosted +3 by peace, clamped to real max 2 (level+1)
    assert {t["key"] for t in s["tablets"]} == {"peace"}
    assert s["approximated"] == []

def test_format_summary_is_readable_text():
    lay = Layout(slot_count=12, tablets=[],
                 artifacts=[ArtifactPlacement("fire_bolt", 0, 0)])
    txt = format_summary(build_summary(lay, "yinggalbul", GD))
    assert "yinggalbul" in txt
    assert "fire_bolt" in txt
    assert "score" in txt.lower()
