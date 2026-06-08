from pydantic import BaseModel, Field


class SolveRequest(BaseModel):
    tablets: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    combo: str
    slots: int
    seed: int = 0
    generations: int = 60
    pop_size: int = 40
