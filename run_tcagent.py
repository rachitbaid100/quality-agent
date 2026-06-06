from __future__ import annotations

import argparse
from pathlib import Path
import sys

from tcagent.cache import DEFAULT_CACHE_PATH, LocalCache
from tcagent.excel_exporter import export_test_cases_to_excel
from tcagent.ollama_client import LocalGenerationError
from tcagent.service import generate_test_cases_text


story = "A new login page supports Google, Apple, and Facebook login"

criteria = (
    "Users can sign in with each provider. "
    "Failed provider auth returns user to login page. "
    "Successful login redirects to dashboard."
)

output_format = "json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run TC-Agent with predefined story and criteria.")
    parser.add_argument("--excel", action="store_true", help="Export cached test cases to Excel by cache key.")
    parser.add_argument("--cachekey", help="Cache key to export when using --excel.")
    parser.add_argument("--output", type=Path, help="Optional output path.")
    return parser


def export_cached_excel(cache_key: str, output_path: Path | None) -> int:
    cache_entry = LocalCache(DEFAULT_CACHE_PATH).get_by_key(cache_key)
    if cache_entry is None:
        print("Cache key not present.")
        return 1

    destination = output_path or Path("exports") / f"test-cases-{cache_key[:12]}.xlsx"
    if destination.exists():
        print(f"Excel file already exists: {destination}")
        return 0

    export_test_cases_to_excel(cache_entry.result, destination)
    print(f"Excel file created: {destination}")
    return 0


if __name__ == "__main__":
    args = build_parser().parse_args()
    if args.excel:
        if not args.cachekey:
            sys.exit("Error: --cachekey is required when using --excel.")
        raise SystemExit(export_cached_excel(args.cachekey, args.output))

    try:
        print(
            generate_test_cases_text(
                story,
                criteria,
                output_format=output_format,
            )
        )
    except LocalGenerationError as exc:
        sys.exit(f"Error: {exc}")
