from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .models import CacheHit, GenerationInput
from .prompt import PROMPT_VERSION


DEFAULT_CACHE_PATH = Path(".tca_cache/cache.json")


@dataclass(frozen=True)
class CacheEntry:
    key: str
    normalized_text: str
    model: str
    prompt_version: str
    result: dict[str, Any]
    created_at: str


class LocalCache:
    def __init__(self, path: Path = DEFAULT_CACHE_PATH):
        self.path = path

    def get(self, data: GenerationInput, similarity_threshold: float) -> CacheHit | None:
        normalized = normalize_text(data.combined_text())
        key = cache_key(data)
        best_entry: CacheEntry | None = None
        best_similarity = 0.0

        for entry in self._read_entries():
            if entry.model != data.model or entry.prompt_version != PROMPT_VERSION:
                continue
            if entry.key == key:
                return CacheHit(entry.result, "exact", 1.0, entry.created_at)

            similarity = SequenceMatcher(None, normalized, entry.normalized_text).ratio()
            if similarity > best_similarity:
                best_entry = entry
                best_similarity = similarity

        if best_entry and best_similarity >= similarity_threshold:
            return CacheHit(best_entry.result, "similar", best_similarity, best_entry.created_at)

        return None

    def set(self, data: GenerationInput, result: dict[str, Any]) -> None:
        entries = [entry for entry in self._read_entries() if entry.key != cache_key(data)]
        entries.append(
            CacheEntry(
                key=cache_key(data),
                normalized_text=normalize_text(data.combined_text()),
                model=data.model,
                prompt_version=PROMPT_VERSION,
                result=result,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"entries": [asdict(entry) for entry in entries]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get_by_key(self, key: str) -> CacheEntry | None:
        for entry in self._read_entries():
            if entry.key == key:
                return entry
        return None

    def _read_entries(self) -> list[CacheEntry]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [CacheEntry(**entry) for entry in payload.get("entries", [])]


def cache_key(data: GenerationInput) -> str:
    material = "|".join(
        [
            data.model,
            PROMPT_VERSION,
            normalize_text(data.combined_text()),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def normalize_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())
