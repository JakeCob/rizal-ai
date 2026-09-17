"""Reflection prompt, version 1.

Bump PROMPT_VERSION whenever the wording changes; it is part of the cache
key, so every cached reflection regenerates on the next request.
"""

import hashlib
import uuid

from rizalai.generation.schema import PassageForPrompt

PROMPT_VERSION = "v1"

SYSTEM = """You write a short reflection in the voice of Jose Rizal for a language learning app. \
The learner has just finished a lesson built on a scene from one of Rizal's novels.

Write the reflection in modern Tagalog first, then render that same reflection in English. \
The Tagalog must read as natural, spoken Tagalog of today, not as translated English. \
Use the Rizal-era passages given as style context to catch his tone: reflective, wry, \
affectionate toward the country, never preachy. Keep to one paragraph of four to six sentences \
in each language.

Rules that cannot be broken:
1. You may quote Rizal's own words only from the CITABLE passages, and only verbatim. \
Every quotation you use must be listed in quoted_spans with the exact text and the passage id it came from. \
Do not quote anything from the STYLE CONTEXT passages. Do not invent quotations, dates, letters, or events.
2. If you do not quote, leave quoted_spans empty. A reflection with no quotes is fine.
3. Do not use em dashes. Use commas, colons, or parentheses.
4. Speak in the first person as Rizal reflecting on the scene, but do not claim to remember things \
that are not in the passages.
"""


def _block(title: str, passages: list[PassageForPrompt], citable: bool) -> str:
    lines = [f"## {title}"]
    for p in passages:
        head = f"[passage_id: {p.id}] " if citable else ""
        lines.append(f"{head}({p.language}, chapter {p.chapter}, paragraph {p.paragraph_index})\n{p.text}\n")
    return "\n".join(lines)


def build_reflection_prompt(
    *, lesson_title: str, vignette_en: str, pinned: list[PassageForPrompt], style: list[PassageForPrompt]
) -> tuple[str, str]:
    user = "\n\n".join(
        [
            f"# Lesson: {lesson_title}",
            f"## What the learner just read (our adaptation, not Rizal's text)\n{vignette_en}",
            _block("CITABLE passages (Rizal's text and its translations)", pinned, citable=True),
            _block("STYLE CONTEXT (tone only, never quote)", style, citable=False),
            "Now write the reflection: tl first, then en, then quoted_spans.",
        ]
    )
    return SYSTEM, user


def reflection_cache_key(lesson_id: uuid.UUID, lesson_version: str, prompt_version: str, model: str) -> str:
    raw = f"reflection|{lesson_id}|{lesson_version}|{prompt_version}|{model}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
