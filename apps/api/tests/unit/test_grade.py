"""Behaviors for grade_response (DECISIONS.md D34):
- Given a token exercise, when the tapped tokens equal answer_tokens or any
  listed accepted order, compared case-insensitively, then correct; any other
  sequence is wrong. The case table is shared with the web grader.
- Given an answer row seeded before accepted_orders existed, then it grades on
  answer_tokens alone.
- Given tokens that are not a list of strings, then wrong, never an error.
- Given comprehension_mc, then the option index decides, as before.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from rizalai.progress.rules import grade_response

CASES_FILE = Path(__file__).resolve().parents[4] / "packages" / "contracts" / "grading-cases.json"
CASES: list[dict[str, Any]] = json.loads(CASES_FILE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_shared_grading_cases(case):
    answer = {"answer_tokens": case["answer_tokens"], "accepted_orders": case["accepted_orders"]}
    assert grade_response(case["type"], answer, {"tokens": case["tokens"]}) is case["correct"]


def test_case_table_covers_every_token_type():
    assert {case["type"] for case in CASES} == {"sentence_assembly", "translate_line", "listen_tap"}


def test_missing_accepted_orders_grades_on_answer_tokens():
    answer = {"answer_tokens": ["Dumating", "ang", "isang", "binata"]}
    assert grade_response("sentence_assembly", answer, {"tokens": ["dumating", "ang", "isang", "binata"]})
    assert not grade_response("sentence_assembly", answer, {"tokens": ["isang", "binata", "ang", "Dumating"]})


@pytest.mark.parametrize(
    "response",
    [{}, {"tokens": None}, {"tokens": "Dumating ang isang binata"}, {"tokens": [1, 2, 3, 4]}],
    ids=["missing", "none", "string", "not strings"],
)
def test_malformed_tokens_grade_wrong(response):
    answer = {"answer_tokens": ["Dumating", "ang", "isang", "binata"], "accepted_orders": []}
    assert grade_response("sentence_assembly", answer, response) is False


def test_malformed_accepted_orders_are_ignored():
    answer = {"answer_tokens": ["Dumating", "ang", "isang", "binata"], "accepted_orders": "oops"}
    assert grade_response("sentence_assembly", answer, {"tokens": ["Dumating", "ang", "isang", "binata"]})
    assert not grade_response("sentence_assembly", answer, {"tokens": ["o", "o", "p", "s"]})


def test_comprehension_mc_is_unchanged():
    answer = {"correct_index": 1}
    assert grade_response("comprehension_mc", answer, {"optionIndex": 1}) is True
    assert grade_response("comprehension_mc", answer, {"optionIndex": 0}) is False
    assert grade_response("comprehension_mc", answer, {"tokens": ["1"]}) is False


@pytest.mark.parametrize("index", [True, 1.0, "1", None], ids=["bool", "float", "string", "none"])
def test_comprehension_mc_requires_an_int_index(index):
    """Mirror of the web grader's strict equality: true is not index 1."""
    assert grade_response("comprehension_mc", {"correct_index": 1}, {"optionIndex": index}) is False
