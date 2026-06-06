from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .cache import DEFAULT_CACHE_PATH
from .local_runtime import mlx_status
from .ollama_client import LocalGenerationError, get_default_model, get_ollama_tags, get_ollama_url
from .service import generate_test_cases_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tcagent",
        description="Generate local Ollama-backed QA test cases with local caching.",
    )
    parser.add_argument("--story", help="User story to generate test cases for.")
    parser.add_argument("--criteria", help="Acceptance criteria for the user story.")
    parser.add_argument("--model", default=get_default_model(), help="Ollama model to use.")
    parser.add_argument("--runtime-info", action="store_true", help="Show local runtime information and exit.")
    parser.add_argument("--doctor", action="store_true", help="Check local Ollama connectivity and exit.")
    parser.add_argument("--cache-path", type=Path, default=DEFAULT_CACHE_PATH, help="Local cache file path.")
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache lookup and refresh the stored result.")
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.94,
        help="Similarity threshold for reusing cached results. Default: 0.94.",
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format.")
    parser.add_argument("--output", type=Path, help="Optional file path for generated output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.runtime_info:
        sys.stdout.write(str(mlx_status()) + "\n")
        return 0

    if args.doctor:
        try:
            tags = get_ollama_tags()
        except LocalGenerationError as exc:
            parser.exit(status=1, message=f"Error: {exc}\n")

        models = [model.get("name") for model in tags.get("models", [])]
        sys.stdout.write(f"Ollama URL: {get_ollama_url()}\n")
        sys.stdout.write(f"Models: {', '.join(models) if models else '(none)'}\n")
        return 0

    story = args.story or input("Paste user story: ").strip()
    criteria = args.criteria or input("Paste acceptance criteria: ").strip()
    if not story or not criteria:
        parser.exit(status=2, message="Error: both user story and acceptance criteria are required.\n")

    try:
        rendered = generate_test_cases_text(
            story,
            criteria,
            output_format=args.format,
            model=args.model,
            cache_path=args.cache_path,
            use_cache=not args.no_cache,
            similarity_threshold=args.similarity_threshold,
        )
    except LocalGenerationError as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered + "\n")

    return 0
