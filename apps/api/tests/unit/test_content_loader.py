"""Behaviors:
- Given the real content directory, when loaded, then every unit and lesson
  file validates and lessons keep their listed order.
- Given a lesson, when hashed twice, then the hash is stable; when any field
  changes, the hash changes.
- Given slugs and keys, when ids are derived, then they are deterministic.
"""

import copy
from pathlib import Path

from rizalai.content.loader import content_hash, exercise_id, lesson_id, load_content, unit_id
from rizalai.contracts.lesson import LessonContent
from tests.fixtures.lesson_example import LESSON_EXAMPLE

CONTENT_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "content"
REAL_CONTENT_DIR = Path(__file__).resolve().parents[3].parent / "content"


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


def test_real_content_directory_validates():
    """The authored content under content/ must always load. Every published
    lesson pins source passages so the Rizal's voice card has something to
    show, and every beat with an exercise_after points at a real exercise
    (checked by the contract)."""
    units = load_content(REAL_CONTENT_DIR)
    assert units, "no units found"
    published = [lesson for unit in units for lesson in unit.lessons if lesson.published]
    assert published, "no published lesson"
    for lesson in published:
        assert lesson.source_passages, lesson.slug
        assert {e.type for e in lesson.exercises} == {
            "sentence_assembly",
            "translate_line",
            "listen_tap",
            "comprehension_mc",
        }, f"{lesson.slug} should exercise all four types"
