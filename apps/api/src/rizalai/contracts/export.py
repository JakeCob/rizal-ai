"""Export the API contracts as one JSON Schema document.

The web app generates TypeScript types from this file, so the two sides
cannot drift. Output is deterministic: sorted keys, fixed indent, trailing
newline.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from rizalai.contracts.lesson import ComprehensionMC, LessonOut, ListenTap, SentenceAssembly, TranslateLine
from rizalai.contracts.tree import Tree
from rizalai.contracts.user import UserOut

TOP_LEVEL: list[type[BaseModel]] = [
    LessonOut,
    Tree,
    UserOut,
    SentenceAssembly,
    TranslateLine,
    ListenTap,
    ComprehensionMC,
]


def _mark_all_required(schema: dict[str, Any]) -> None:
    """The API serializes every field, defaults included, so for the consumer
    every property is present. Pydantic only lists fields without defaults
    as required; widen that so the generated TypeScript has no spurious
    optionals."""
    for definition in schema.get("$defs", {}).values():
        props = definition.get("properties")
        if isinstance(props, dict) and props:
            definition["required"] = sorted(props.keys())


def build_schema() -> dict[str, Any]:
    _, schema = models_json_schema(
        [(model, "serialization") for model in TOP_LEVEL],
        title="RizalAI API contracts",
        ref_template="#/$defs/{model}",
    )
    result: dict[str, Any] = dict(schema)
    _mark_all_required(result)
    return result


def export_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../../packages/contracts/schema.json")
    export_schema(target)
    print(f"wrote {target}")
