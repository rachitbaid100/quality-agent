from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GenerationInput:
    user_story: str
    acceptance_criteria: str
    model: str

    def combined_text(self) -> str:
        return f"User Story:\n{self.user_story}\n\nAcceptance Criteria:\n{self.acceptance_criteria}"


@dataclass(frozen=True)
class CacheHit:
    result: dict[str, Any]
    match_type: str
    similarity: float
    cached_at: str

