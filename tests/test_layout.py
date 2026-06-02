from sota.model.layout import TabletPlacement, ArtifactPlacement, Layout

def test_artifact_lookup_and_iteration():
    lay = Layout(
        slot_count=12,
        tablets=[TabletPlacement(key="peace", row=1, col=1, rotation=0)],
        artifacts=[ArtifactPlacement(key="fire_bolt", row=1, col=0),
                   ArtifactPlacement(key="ohia_lehua", row=1, col=2)],
    )
    assert lay.artifact_at(1, 0).key == "fire_bolt"
    assert lay.artifact_at(0, 0) is None
    assert {a.key for a in lay.artifacts} == {"fire_bolt", "ohia_lehua"}
    assert lay.tablets[0].rotation == 0

def test_rejects_two_items_on_one_cell():
    import pytest
    with pytest.raises(ValueError):
        Layout(slot_count=12,
               tablets=[TabletPlacement(key="peace", row=0, col=0, rotation=0)],
               artifacts=[ArtifactPlacement(key="fire_bolt", row=0, col=0)])
