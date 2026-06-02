from dataclasses import dataclass, field

@dataclass(frozen=True)
class TabletPlacement:
    key: str
    row: int
    col: int
    rotation: int = 0

@dataclass(frozen=True)
class ArtifactPlacement:
    key: str
    row: int
    col: int

@dataclass
class Layout:
    slot_count: int
    tablets: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)

    def __post_init__(self):
        seen = set()
        for p in list(self.tablets) + list(self.artifacts):
            cell = (p.row, p.col)
            if cell in seen:
                raise ValueError(f"two items on cell {cell}")
            seen.add(cell)
        self._art_by_cell = {(a.row, a.col): a for a in self.artifacts}

    def artifact_at(self, row: int, col: int):
        return self._art_by_cell.get((row, col))
