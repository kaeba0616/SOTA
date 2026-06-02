from sota.evaluate.effects import rotate_pos, pos_target
from sota.model.grid import Grid

def test_rotate_pos_90_steps():
    assert rotate_pos([1, 0], 0) == (1, 0)
    assert rotate_pos([1, 0], 1) == (0, -1)
    assert rotate_pos([1, 0], 2) == (-1, 0)
    assert rotate_pos([1, 0], 3) == (0, 1)
    assert rotate_pos([1, 2], 1) == (2, -1)

def test_pos_target_uses_up_positive_dy():
    g = Grid(36)
    assert pos_target(3, 3, [-1, 2], 0, g) == (1, 2)
    assert pos_target(0, 0, [0, 1], 0, g) is None
