"""Behaviors for the reflection prompt (DECISIONS.md D02, D03):
- the pinned passages appear with their ids so the model can cite them
- style context passages are labeled as style only, never citable
- the instruction orders Tagalog first, then English
- the prompt forbids em dashes and invented quotations
- the cache key is deterministic and changes with any input
"""

import uuid

from rizalai.generation.prompt import PROMPT_VERSION, build_reflection_prompt, reflection_cache_key
from rizalai.generation.schema import PassageForPrompt

LESSON_ID = uuid.uuid4()


def _passage(lang: str, text: str, chapter: int = 2, idx: int = 3) -> PassageForPrompt:
    return PassageForPrompt(id=uuid.uuid4(), language=lang, chapter=chapter, paragraph_index=idx, text=text)


def test_prompt_contains_pinned_passages_with_ids_and_style_context():
    pinned = [_passage("es", "Tengo el honor de presentar"), _passage("tl", "May capurihan acóng ipakilala")]
    style = [_passage("tl", "Umaaticabong nan~gagsasalitaan ang iláng m~ga cadete")]
    system, user = build_reflection_prompt(
        lesson_title="Ibarra arrives at the dinner",
        vignette_en="Capitan Tiago presents Ibarra.",
        pinned=pinned,
        style=style,
    )
    for p in pinned:
        assert str(p.id) in user and p.text in user
    assert style[0].text in user
    assert str(style[0].id) not in user  # style passages are not citable
    assert "Tagalog first" in system or "Tagalog" in system.split("English")[0]
    assert "verbatim" in system
    assert "—" not in system and "—" not in user


def test_prompt_version_is_pinned():
    assert PROMPT_VERSION == "v1"


def test_cache_key_is_deterministic_and_sensitive():
    a = reflection_cache_key(LESSON_ID, "abc", "v1", "claude-opus-5")
    assert a == reflection_cache_key(LESSON_ID, "abc", "v1", "claude-opus-5")
    assert len(a) == 64
    assert a != reflection_cache_key(LESSON_ID, "abd", "v1", "claude-opus-5")
    assert a != reflection_cache_key(LESSON_ID, "abc", "v2", "claude-opus-5")
    assert a != reflection_cache_key(LESSON_ID, "abc", "v1", "other-model")
