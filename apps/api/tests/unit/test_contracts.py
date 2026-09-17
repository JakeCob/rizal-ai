"""Behaviors for the lesson contract, the one schema that content YAML, the
database, the API, and four React components all depend on.

- Given a well-formed lesson dict, when validated, then it round-trips.
- Given an exercise with an unknown type, when validated, then it is rejected.
- Given a sentence_assembly whose answer tokens are not all in the bank,
  when validated, then it is rejected.
- Given a comprehension_mc whose correct_index is out of range, when
  validated, then it is rejected.
- Given a published lesson with too few beats or exercises, when validated,
  then it is rejected; an unpublished stub is allowed.
- Given the export function, when run twice, then the JSON Schema is
  byte-identical and names the top-level API types.
"""

import copy
import json

import pytest
from pydantic import ValidationError

from rizalai.contracts.export import export_schema
from rizalai.contracts.lesson import Exercise, ExerciseAdapter, LessonContent
from tests.fixtures.lesson_example import LESSON_EXAMPLE


def test_example_lesson_round_trips():
    lesson = LessonContent.model_validate(LESSON_EXAMPLE)
    assert lesson.slug == "scaffold-placeholder"
    assert len(lesson.vignette) == 4
    assert [e.type for e in lesson.exercises] == [
        "sentence_assembly",
        "translate_line",
        "listen_tap",
        "comprehension_mc",
        "sentence_assembly",
        "comprehension_mc",
    ]
    assert lesson.model_dump(mode="json")["exercises"][0]["key"] == "ex1"


def test_unknown_exercise_type_is_rejected():
    with pytest.raises(ValidationError):
        ExerciseAdapter.validate_python({"type": "word_picture", "key": "x", "xp": 10})


def test_sentence_assembly_answer_must_be_drawn_from_bank():
    bad = {
        "type": "sentence_assembly",
        "key": "x",
        "prompt_en": "He arrived.",
        "answer_tokens": ["Dumating", "siya"],
        "bank": ["Dumating", "kami"],
    }
    with pytest.raises(ValidationError, match="bank"):
        ExerciseAdapter.validate_python(bad)


def test_sentence_assembly_bank_must_cover_repeated_tokens():
    bad = {
        "type": "sentence_assembly",
        "key": "x",
        "prompt_en": "Very very good.",
        "answer_tokens": ["Napaka", "napaka", "buti"],
        "bank": ["Napaka", "buti", "napaka"],
    }
    ok: Exercise = ExerciseAdapter.validate_python(bad)
    assert ok.type == "sentence_assembly"
    bad["bank"] = ["Napaka", "buti"]
    with pytest.raises(ValidationError, match="bank"):
        ExerciseAdapter.validate_python(bad)


def test_comprehension_mc_index_must_be_in_range():
    bad = {
        "type": "comprehension_mc",
        "key": "x",
        "question": "Who?",
        "options": ["Ibarra", "Tiago"],
        "correct_index": 2,
    }
    with pytest.raises(ValidationError, match="correct_index"):
        ExerciseAdapter.validate_python(bad)


def test_exercise_keys_must_be_unique_within_lesson():
    data = copy.deepcopy(LESSON_EXAMPLE)
    data["exercises"][1]["key"] = data["exercises"][0]["key"]
    with pytest.raises(ValidationError, match="unique"):
        LessonContent.model_validate(data)


def test_published_lesson_needs_enough_beats_and_exercises():
    data = copy.deepcopy(LESSON_EXAMPLE)
    data["vignette"] = data["vignette"][:2]
    with pytest.raises(ValidationError, match="4 to 8"):
        LessonContent.model_validate(data)

    data = copy.deepcopy(LESSON_EXAMPLE)
    data["exercises"] = data["exercises"][:3]
    with pytest.raises(ValidationError, match="6 to 12"):
        LessonContent.model_validate(data)


def test_unpublished_stub_lesson_is_allowed():
    stub = {
        "slug": "noli-ch02-placeholder",
        "title": "Chapter 2 (coming soon)",
        "published": False,
        "estimated_minutes": 5,
    }
    lesson = LessonContent.model_validate(stub)
    assert lesson.vignette == []
    assert lesson.exercises == []


def test_beat_exercise_after_must_reference_existing_key():
    data = copy.deepcopy(LESSON_EXAMPLE)
    data["vignette"][1]["exercise_after"] = "does-not-exist"
    with pytest.raises(ValidationError, match="exercise_after"):
        LessonContent.model_validate(data)


def test_export_is_deterministic_and_names_api_types(tmp_path):
    out = tmp_path / "schema.json"
    export_schema(out)
    first = out.read_bytes()
    export_schema(out)
    assert out.read_bytes() == first
    schema = json.loads(first)
    for name in ("LessonOut", "Tree", "UserOut", "SentenceAssembly", "ComprehensionMC"):
        assert name in schema["$defs"], name


def test_passage_ref_accepts_optional_alignment_group():
    from rizalai.contracts.lesson import PassageRef

    ref = PassageRef.model_validate(
        {"work": "noli", "language": "es", "chapter": 2, "paragraph_index": 3, "group": "intro"}
    )
    assert ref.group == "intro"
    assert (
        PassageRef.model_validate(
            {"work": "noli", "language": "tl", "chapter": 2, "paragraph_index": 3}
        ).group
        is None
    )
