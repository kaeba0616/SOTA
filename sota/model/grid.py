import math

class Grid:
    cols = 6

    def __init__(self, slot_count: int):
        if slot_count < 1:
            raise ValueError("slot_count must be >= 1")
        self.slot_count = slot_count
        self.rows = math.ceil(slot_count / self.cols)

    def index(self, r: int, c: int) -> int:
        return r * self.cols + c

    def is_valid(self, r: int, c: int) -> bool:
        if r < 0 or c < 0 or c >= self.cols or r >= self.rows:
            return False
        return self.index(r, c) < self.slot_count

    def cells(self):
        for i in range(self.slot_count):
            yield divmod(i, self.cols)
