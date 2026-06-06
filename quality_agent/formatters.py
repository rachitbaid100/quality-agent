from __future__ import annotations

import json
from typing import Any


def render_result(result: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(result, indent=2)
    if output_format == "markdown":
        return render_markdown(result)
    raise ValueError(f"Unsupported output format: {output_format}")


def render_markdown(result: dict[str, Any]) -> str:
    lines = ["# Generated Test Cases", ""]
    summary = result.get("summary")
    if summary:
        lines.extend([str(summary), ""])

    for index, case in enumerate(result.get("test_cases", []), start=1):
        lines.extend(
            [
                f"## TC-{index:03d}: {case.get('title', 'Untitled')}",
                f"- Category: {case.get('category', '')}",
                f"- Priority: {case.get('priority', '')}",
                "- Preconditions:",
            ]
        )
        lines.extend([f"  - {item}" for item in case.get("preconditions", [])])
        lines.append("- Steps:")
        lines.extend([f"  {step_index}. {step}" for step_index, step in enumerate(case.get("steps", []), start=1)])
        lines.extend([f"- Expected Result: {case.get('expected_result', '')}", ""])

    return "\n".join(lines)

