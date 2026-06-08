from sota.web.schemas import SolveRequest


def test_solve_request_defaults():
    req = SolveRequest(combo="firmness", slots=34)
    assert req.tablets == []
    assert req.artifacts == []
    assert req.seed == 0
    assert req.generations == 60
    assert req.pop_size == 40


def test_solve_request_accepts_items():
    req = SolveRequest(combo="firmness", slots=30,
                       tablets=["agglutination"], artifacts=["amulet_of_power"])
    assert req.tablets == ["agglutination"]
    assert req.artifacts == ["amulet_of_power"]
