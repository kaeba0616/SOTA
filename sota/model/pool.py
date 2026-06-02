from dataclasses import dataclass, field

@dataclass(frozen=True)
class ItemPool:
    tablets: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)

    def candidates(self):
        """Flat ordered list of (kind, key); tablets first, then artifacts."""
        return [("tablet", k) for k in self.tablets] + [("artifact", k) for k in self.artifacts]

    def __len__(self):
        return len(self.tablets) + len(self.artifacts)
