"""Export the API contracts as one JSON Schema document.

The web app generates TypeScript types from this file, so the two sides
cannot drift. Output is deterministic: sorted keys, fixed indent, trailing
newline.
"""

import json
from pathlib import Path

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


def build_schema() -> dict[str, object]:
    _, schema = models_json_schema(
        [(model, "serialization") for model in TOP_LEVEL],
        title="RizalAI API contracts",
        ref_template="#/$defs/{model}",
    )
    return dict(schema)


def export_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../../packages/contracts/schema.json")
    export_schema(target)
    print(f"wrote {target}")
