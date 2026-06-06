from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .cache import DEFAULT_CACHE_PATH, LocalCache
from .formatters import render_result
from .models import GenerationInput
from .ollama_client import generate_with_ollama, get_default_model

Generator = Callable[[GenerationInput], dict[str, Any]]


def generate_test_cases(
    user_story: str,
    acceptance_criteria: str,
    *,
    model: str | None = None,
    cache_path: Path = DEFAULT_CACHE_PATH,
    use_cache: bool = True,
    similarity_threshold: float = 0.94,
    generator: Generator = generate_with_ollama,
) -> dict[str, Any]:
    if not user_story.strip() or not acceptance_criteria.strip():
        raise ValueError("Both user story and acceptance criteria are required.")

    data = GenerationInput(
        user_story=user_story.strip(),
        acceptance_criteria=acceptance_criteria.strip(),
        model=model or get_default_model(),
    )
    cache = LocalCache(cache_path)

    cache_hit = cache.get(data, similarity_threshold) if use_cache else None
    if cache_hit:
        return {
            **cache_hit.result,
            "_cache": {
                "hit": True,
                "match_type": cache_hit.match_type,
                "similarity": round(cache_hit.similarity, 4),
                "cached_at": cache_hit.cached_at,
            },
        }

    result = generator(data)
    cache.set(data, result)
    return {**result, "_cache": {"hit": False, "model": data.model}}


def generate_test_cases_text(
    user_story: str,
    acceptance_criteria: str,
    *,
    output_format: str = "json",
    model: str | None = None,
    cache_path: Path = DEFAULT_CACHE_PATH,
    use_cache: bool = True,
    similarity_threshold: float = 0.94,
    generator: Generator = generate_with_ollama,
) -> str:
    result = generate_test_cases(
        user_story,
        acceptance_criteria,
        model=model,
        cache_path=cache_path,
        use_cache=use_cache,
        similarity_threshold=similarity_threshold,
        generator=generator,
    )
    return render_result(result, output_format)
