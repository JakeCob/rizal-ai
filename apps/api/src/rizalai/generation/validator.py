"""The mechanical half of the no-hallucinated-Rizal rule (DECISIONS.md D03).

A quoted span is valid only if it is a verbatim substring of the passage it
cites. Whitespace is normalized on both sides; nothing else is forgiven,
not case, not punctuation, not accents.
"""

import re
import uuid

from rizalai.generation.schema import ReflectionDraft

_WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _WS.sub(" ", text).strip()


def validate_citations(draft: ReflectionDraft, passages: dict[uuid.UUID, str]) -> list[str]:
    errors: list[str] = []
    normalized = {pid: _norm(text) for pid, text in passages.items()}
    for i, span in enumerate(draft.quoted_spans):
        source = normalized.get(span.passage_id)
        if source is None:
            errors.append(f"span {i}: unknown passage {span.passage_id}")
            continue
        if _norm(span.text) not in source:
            errors.append(
                f"span {i}: not a verbatim substring of passage {span.passage_id}: {span.text[:60]!r}"
            )
    return errors
