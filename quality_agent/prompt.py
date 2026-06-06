from __future__ import annotations

from .models import GenerationInput


PROMPT_VERSION = "quality-agent-v1-compact-json"


def build_generation_prompt(data: GenerationInput) -> str:
    return f"""Generate QA test cases from the input.

Rules:
- Return JSON only. No markdown. No commentary.
- Generate at most 12 high-value test cases.
- Avoid duplicate provider-only repetition unless behavior differs.
- Cover positive, negative, edge, security, integration, and API scenarios when applicable.
- Keep every field concise.
- Use priority values P0, P1, or P2.

JSON shape:
{{
  "summary": "short feature summary",
  "test_cases": [
    {{
      "title": "string",
      "category": "positive|negative|edge|security|integration|api",
      "priority": "P0|P1|P2",
      "preconditions": ["string"],
      "steps": ["string"],
      "expected_result": "string"
    }}
  ]
}}

Input:
{data.combined_text()}
"""
