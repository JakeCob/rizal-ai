"""Get or generate the reflection for a lesson (DECISIONS.md D02, D03, D04, D21).

Cache key: (lesson id, lesson version, prompt version, model). A published
or fallback row is returned as is. A missing or rejected row triggers one
generation, validated by the citation check; on failure the model gets one
more try, then the row is stored as fallback and the card shows passages
only. The judge score is left null until the threshold is set (D21).
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.corpus.retrieval import pinned_passages, style_context
from rizalai.db.models import GeneratedContentCache, Lesson, SourcePassage
from rizalai.generation.llm import LLMClient, LLMError
from rizalai.generation.prompt import PROMPT_VERSION, build_reflection_prompt, reflection_cache_key
from rizalai.generation.schema import (
    LayerOut,
    PassageForPrompt,
    PassageOut,
    ReflectionDraft,
    ReflectionOut,
)
from rizalai.generation.validator import validate_citations

log = logging.getLogger(__name__)

MAX_GENERATION_ATTEMPTS = 2

LAYER_LABELS = {
    ("es", None): "Spanish (Rizal's original, 1887)",
    ("tl", "poblete_1909"): "Tagalog (Pascual Poblete's 1909 translation)",
    ("en", "derbyshire_1912"): "English (Charles Derbyshire's 1912 translation)",
}


def build_layers(passages: list[SourcePassage]) -> list[LayerOut]:
    layers: dict[tuple[str, str | None], LayerOut] = {}
    for p in passages:
        key = (p.language, p.translator)
        if key not in layers:
            label = LAYER_LABELS.get(key, f"{p.language} ({p.translator or 'original'})")
            layers[key] = LayerOut.model_validate(
                {"language": p.language, "translator": p.translator, "label": label, "passages": []}
            )
        layers[key].passages.append(
            PassageOut(id=p.id, chapter=p.chapter, paragraph_index=p.paragraph_index, text=p.text)
        )
    return list(layers.values())


def _for_prompt(p: SourcePassage) -> PassageForPrompt:
    return PassageForPrompt(
        id=p.id, language=p.language, chapter=p.chapter, paragraph_index=p.paragraph_index, text=p.text
    )


def _out(lesson: Lesson, layers: list[LayerOut], row: GeneratedContentCache) -> ReflectionOut:
    reflection = ReflectionDraft.model_validate(row.content) if row.status == "published" else None
    return ReflectionOut(
        lesson_id=lesson.id,
        status="published" if row.status == "published" else "fallback",
        layers=layers,
        reflection=reflection,
        model=row.model,
        prompt_version=row.prompt_version,
    )


async def _generate(
    session: AsyncSession, lesson: Lesson, pinned: list[SourcePassage], llm: LLMClient
) -> tuple[ReflectionDraft | None, bool]:
    chapters = sorted({p.chapter for p in pinned if p.language == "tl"}) or sorted(
        {p.chapter for p in pinned}
    )
    style = await style_context(
        session, work="noli", language="tl", chapters=chapters, exclude=[p.id for p in pinned], limit=3
    )
    vignette_en = " ".join(str(b.get("en", "")) for b in lesson.vignette)
    system, user = build_reflection_prompt(
        lesson_title=lesson.title,
        vignette_en=vignette_en,
        pinned=[_for_prompt(p) for p in pinned],
        style=[_for_prompt(p) for p in style],
    )
    texts = {p.id: p.text for p in pinned}
    for attempt in range(MAX_GENERATION_ATTEMPTS):
        try:
            draft = await llm.generate(system, user, ReflectionDraft)
        except LLMError as exc:
            log.warning("reflection generation failed for %s (attempt %d): %s", lesson.slug, attempt + 1, exc)
            continue
        errors = validate_citations(draft, texts)
        if not errors:
            return draft, True
        log.warning("reflection citations invalid for %s (attempt %d): %s", lesson.slug, attempt + 1, errors)
    return None, False


async def get_or_generate_reflection(session: AsyncSession, lesson: Lesson, llm: LLMClient) -> ReflectionOut:
    pinned = await pinned_passages(session, lesson.source_passage_ids)
    layers = build_layers(pinned)
    key = reflection_cache_key(lesson.id, lesson.version, PROMPT_VERSION, llm.model)
    row = await session.scalar(select(GeneratedContentCache).where(GeneratedContentCache.cache_key == key))
    if row is not None and row.status in ("published", "fallback"):
        return _out(lesson, layers, row)

    draft, valid = await _generate(session, lesson, pinned, llm)
    values = {
        "kind": "reflection",
        "cache_key": key,
        "content": draft.model_dump(mode="json") if (draft and valid) else {},
        "citations_valid": valid,
        "judge_score": None,
        "status": "published" if valid else "fallback",
        "model": llm.model,
        "prompt_version": PROMPT_VERSION,
    }
    stmt = insert(GeneratedContentCache).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["cache_key"], set_={k: v for k, v in values.items() if k != "cache_key"}
    )
    await session.execute(stmt)
    await session.commit()
    # populate_existing: the upsert went through Core, so an identity-mapped
    # row from the earlier select would otherwise keep its stale status.
    row = await session.scalar(
        select(GeneratedContentCache)
        .where(GeneratedContentCache.cache_key == key)
        .execution_options(populate_existing=True)
    )
    assert row is not None
    return _out(lesson, layers, row)


async def reject_reflection(session: AsyncSession, cache_id: uuid.UUID) -> bool:
    row = await session.get(GeneratedContentCache, cache_id)
    if row is None:
        return False
    row.status = "rejected"
    await session.commit()
    return True


async def list_reflections(session: AsyncSession) -> list[GeneratedContentCache]:
    return list(
        (
            await session.scalars(
                select(GeneratedContentCache).order_by(GeneratedContentCache.created_at.desc())
            )
        ).all()
    )
