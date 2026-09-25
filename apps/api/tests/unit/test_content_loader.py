"""Behaviors:
- Given the real content directory, when loaded, then every unit and lesson
  file validates and lessons keep their listed order.
- Given a lesson, when hashed twice, then the hash is stable; when any field
  changes, the hash changes.
- Given slugs and keys, when ids are derived, then they are deterministic.
- Given the real content directory, when checked for authoring mistakes, then
  every published lesson pins es, tl, and en, each group spans at least two
  editions of one chapter, no passage row is pinned twice across the tree,
  each exercise follows at most one beat, every tile is a single token,
  unpublished lessons are empty stubs, unit and lesson slugs are unique, and
  each unit folder's NN- prefix matches its order_index.
"""

import copy
import re
from collections import Counter, defaultdict
from pathlib import Path

import pytest
import yaml

from rizalai.content.loader import UnitContent, content_hash, exercise_id, lesson_id, load_content, unit_id
from rizalai.contracts.lesson import LessonContent, ListenTap, SentenceAssembly, TranslateLine
from tests.fixtures.lesson_example import LESSON_EXAMPLE

CONTENT_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "content"
REAL_CONTENT_DIR = Path(__file__).resolve().parents[3].parent / "content"

# Tiles are split on tokens, so a token must not hide any space, including
# the zero-width and non-breaking kinds that str.isspace() misses or that
# look like a single word on screen.
_HIDDEN_SPACES = {"\u200b", "\u00a0"}


@pytest.fixture(scope="module")
def real_units() -> list[UnitContent]:
    return load_content(REAL_CONTENT_DIR)


def test_fixture_content_directory_loads_in_order():
    units = load_content(CONTENT_DIR)
    assert [u.slug for u in units] == ["test-unit"]
    lessons = units[0].lessons
    assert lessons[0].slug == "scaffold-placeholder"
    assert lessons[0].published is True
    assert all(lesson.published is False for lesson in lessons[1:])
    assert len(lessons) == 4


def test_content_hash_is_stable_and_sensitive():
    lesson = LessonContent.model_validate(LESSON_EXAMPLE)
    assert content_hash(lesson) == content_hash(LessonContent.model_validate(LESSON_EXAMPLE))
    changed = copy.deepcopy(LESSON_EXAMPLE)
    changed["vignette"][0]["tl"] = "Mayroong hapunan sa bahay ni Kapitan Tiago."
    assert content_hash(LessonContent.model_validate(changed)) != content_hash(lesson)
    assert len(content_hash(lesson)) == 64


def test_ids_are_deterministic():
    assert unit_id("noli-arrival") == unit_id("noli-arrival")
    assert lesson_id("a") != lesson_id("b")
    assert exercise_id("scaffold-placeholder", "ex1") == exercise_id("scaffold-placeholder", "ex1")
    assert exercise_id("scaffold-placeholder", "ex1") != exercise_id("scaffold-placeholder", "ex2")
    assert exercise_id("x", "ex1") != exercise_id("y", "ex1")


def test_real_content_directory_validates(real_units):
    """The authored content under content/ must always load. Every published
    lesson pins source passages so the Rizal's voice card has something to
    show, and every beat with an exercise_after points at a real exercise
    (checked by the contract)."""
    assert real_units, "no units found"
    published = [lesson for unit in real_units for lesson in unit.lessons if lesson.published]
    assert published, "no published lesson"
    for lesson in published:
        assert lesson.source_passages, f"{lesson.slug}: no source_passages"
        types = {e.type for e in lesson.exercises}
        assert types == {"sentence_assembly", "translate_line", "listen_tap", "comprehension_mc"}, (
            f"{lesson.slug} should exercise all four types, has {sorted(types)}"
        )


def _lessons(units: list[UnitContent]) -> list[LessonContent]:
    return [lesson for unit in units for lesson in unit.lessons]


def test_published_lessons_groups_span_editions(real_units):
    """Refs sharing a group are the same passage in different editions,
    aligned by content (D19). A passage may have no variant in one edition
    (lesson 1's arrival group has no Tagalog because Poblete's Chapter 1 ends
    in translator notes), so docs/plans/004-unit-one.md sets the rule at two
    or three editions per group, not three. Every ref in a group must share
    one (work, chapter): editions number paragraphs differently, but the same
    passage never moves chapter. No group needs an allowance for that today;
    lesson 1's arrival group pins es 1:89 and en 1:79, both Chapter 1. Every
    ref must carry a group, and every published lesson must still pin es, tl,
    and en across its refs as a whole."""
    problems = []
    for lesson in _lessons(real_units):
        if not lesson.published:
            continue
        languages: dict[str, set[str]] = defaultdict(set)
        chapters: dict[str, set[tuple[str, int]]] = defaultdict(set)
        for ref in lesson.source_passages:
            if ref.group is None:
                problems.append(
                    f"{lesson.slug}: ungrouped ref {ref.language} {ref.chapter}:{ref.paragraph_index}"
                )
                continue
            languages[ref.group].add(ref.language)
            chapters[ref.group].add((ref.work, ref.chapter))
        for group, found in languages.items():
            if len(found) < 2:
                problems.append(f"{lesson.slug} group {group}: has only {sorted(found)}")
        for group, found_chapters in chapters.items():
            if len(found_chapters) > 1:
                problems.append(f"{lesson.slug} group {group}: spans {sorted(found_chapters)}")
        pinned = {ref.language for ref in lesson.source_passages}
        if pinned != {"es", "tl", "en"}:
            problems.append(f"{lesson.slug}: pins only {sorted(pinned)}")
    assert not problems, "\n".join(problems)


def test_passage_locators_are_unique_across_published_lessons(real_units):
    """align_passage_groups stamps one passage_group_id per source_passages
    row, so a row pinned twice (by two lessons, or twice in one) would keep
    only the last group."""
    seen: dict[tuple[str, str, int, int], str] = {}
    problems = []
    for lesson in _lessons(real_units):
        if not lesson.published:
            continue
        for ref in lesson.source_passages:
            locator = (ref.work, ref.language, ref.chapter, ref.paragraph_index)
            if locator in seen:
                problems.append(f"{locator} pinned by {seen[locator]} and {lesson.slug}")
            else:
                seen[locator] = lesson.slug
    assert not problems, "\n".join(problems)


def test_exercise_after_keys_are_used_at_most_once(real_units):
    problems = []
    for lesson in _lessons(real_units):
        keys = Counter(beat.exercise_after for beat in lesson.vignette if beat.exercise_after is not None)
        problems += [
            f"{lesson.slug}: {key} follows {count} beats" for key, count in keys.items() if count > 1
        ]
    assert not problems, "\n".join(problems)


def test_answer_tokens_never_contain_whitespace(real_units):
    problems = []
    for lesson in _lessons(real_units):
        for exercise in lesson.exercises:
            if not isinstance(exercise, SentenceAssembly | TranslateLine | ListenTap):
                continue
            orders = [token for order in exercise.accepted_orders for token in order]
            for token in [*exercise.answer_tokens, *orders, *exercise.bank]:
                if not token or any(ch.isspace() or ch in _HIDDEN_SPACES for ch in token):
                    problems.append(f"{lesson.slug} {exercise.key}: bad token {token!r}")
    assert not problems, "\n".join(problems)


def test_unpublished_lessons_are_empty_stubs(real_units):
    stubs = [lesson for lesson in _lessons(real_units) if not lesson.published]
    assert stubs, "no unpublished lesson found"
    problems = [
        f"{lesson.slug}: {len(lesson.vignette)} beats, {len(lesson.exercises)} exercises, "
        f"{len(lesson.source_passages)} source_passages"
        for lesson in stubs
        if lesson.vignette or lesson.exercises or lesson.source_passages
    ]
    assert not problems, "\n".join(problems)


def test_unit_and_lesson_slugs_are_unique(real_units):
    """Lesson ids are uuid5 of the slug alone, so a lesson slug repeated in
    another unit would overwrite the first lesson at seed time."""
    units = Counter(unit.slug for unit in real_units)
    lessons: dict[str, list[str]] = defaultdict(list)
    for unit in real_units:
        for lesson in unit.lessons:
            lessons[lesson.slug].append(unit.slug)
    problems = [f"unit slug {slug} used {count} times" for slug, count in units.items() if count > 1]
    problems += [
        f"lesson slug {slug} used in units {where}" for slug, where in lessons.items() if len(where) > 1
    ]
    assert not problems, "\n".join(problems)


def test_unit_folder_prefix_matches_order_index(real_units):
    problems = []
    for folder in sorted(p for p in (REAL_CONTENT_DIR / "units").iterdir() if (p / "unit.yaml").exists()):
        unit = yaml.safe_load((folder / "unit.yaml").read_text(encoding="utf-8"))
        prefix = folder.name.split("-", 1)[0]
        if not prefix.isdigit() or int(prefix) != unit["order_index"]:
            problems.append(f"{unit['slug']}: folder {folder.name} but order_index {unit['order_index']}")
    order = defaultdict(list)
    for unit_ in real_units:
        order[unit_.order_index].append(unit_.slug)
    problems += [
        f"order_index {index} shared by units {slugs}" for index, slugs in order.items() if len(slugs) > 1
    ]
    assert not problems, "\n".join(problems)


def test_listen_tap_banks_have_no_case_only_duplicates(real_units):
    """Tiles compare case-insensitively (D34), so a learner working by ear
    cannot tell Galit from galit. Two such tiles are allowed only when the
    transcript uses both."""
    problems = []
    for lesson in _lessons(real_units):
        for exercise in lesson.exercises:
            if not isinstance(exercise, ListenTap):
                continue
            for variants in _case_only_duplicates(exercise):
                problems.append(f"{lesson.slug} {exercise.key}: tiles {sorted(variants)} differ only by case")
    assert not problems, "\n".join(problems)


def _case_only_duplicates(exercise: ListenTap) -> list[set[str]]:
    """Groups of bank tiles equal under lower() that the transcript does not
    use in every spelling."""
    folded: dict[str, set[str]] = defaultdict(set)
    for tile in exercise.bank:
        folded[tile.lower()].add(tile)
    transcript = set(re.findall(r"[\w'-]+", exercise.transcript_tl))
    return [variants for variants in folded.values() if len(variants) > 1 and not variants <= transcript]


def test_case_only_duplicate_check_ignores_punctuation():
    exercise = ListenTap(
        type="listen_tap",
        key="x",
        transcript_tl="Ano? ano raw?",
        answer_tokens=["Ano", "ano", "raw"],
        bank=["Ano", "ano", "raw", "sino"],
    )
    assert _case_only_duplicates(exercise) == []
