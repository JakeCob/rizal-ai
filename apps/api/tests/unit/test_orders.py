"""Behaviors for the order-enumeration helper (plan 006, tasks C and C2).
The exercises come from tests/fixtures/orders_examples.py, frozen copies of
lesson exercises, so re-authoring a lesson cannot break these tests; one
smoke test runs the CLI over a real lesson file.

- Given lesson 2 ex6 in split mode, then the listed alternate is reachable
  and excluded from the candidates; stripped of accepted_orders it becomes a
  candidate and the unlisted count rises by one.
- Given lesson 2 ex3, then zero candidates by the mover rule; with phrases
  and the orders stripped, the trailing-kay order is a candidate; with the
  orders kept, both are reported as listed.
- Given lesson 5 ex4, then 28 unlisted orders in the default block mode and
  1678 with --split; a cap limits the printout, not the count.
- Given split mode without bank or phrases, then the closed-form count is
  exact; in block mode it is an upper bound and is labelled "up to".
- Given flags together, then the orders are the union of what each flag
  reaches alone: never fewer than --split or --phrases by itself.
- Given --bank in block mode, then a particle added or swapped in from the
  bank moves on its own.
- Given more orders than the enumeration limit, then listed orders are still
  reported as reachable or not.
- Given a tl_to_en translate_line, then the English movers apply; --clitics
  is case-insensitive and output keeps the tiles' casing.
- Given the CLI, then listen_tap is skipped by default with one line, a
  comprehension_mc key says it has no word order, an unknown key, a negative
  --max, a missing file or a file that is not a lesson exits with one line.
"""

from pathlib import Path

import pytest
import yaml

from rizalai.cli import main
from rizalai.content import orders
from rizalai.content.orders import (
    DEFAULT_EN_MOVERS,
    DEFAULT_TL_MOVERS,
    candidate_count,
    format_report,
    iter_candidates,
    movers_for,
    report,
)
from rizalai.contracts.lesson import ExerciseAdapter, TokenExercise
from tests.fixtures import orders_examples as ex

REAL_LESSON = (
    Path(__file__).resolve().parents[3].parent / "content" / "units" / "02-san-diego" / "01-the-town.yaml"
)


def _token(data: dict) -> TokenExercise:
    parsed = ExerciseAdapter.validate_python(data)
    assert isinstance(parsed, TokenExercise)
    return parsed


def _words(tokens) -> str:
    return " ".join(tokens).lower()


def _folded(exercise: TokenExercise, **flags) -> set[str]:
    return {_words(o) for o in iter_candidates(exercise, movers_for(exercise), **flags)}


def _lesson_file(tmp_path: Path, *exercises: dict) -> Path:
    """A lesson file holding the given exercises; unpublished, so it needs no beats."""
    path = tmp_path / "probe.yaml"
    lesson = {"slug": "orders-probe", "title": "Probe", "published": False, "exercises": list(exercises)}
    path.write_text(yaml.safe_dump(lesson, allow_unicode=True), encoding="utf-8")
    return path


def test_listed_alternate_is_reachable_and_excluded():
    exercise = _token(ex.L2_EX6)
    result = report(exercise, split=True)
    assert "mula pa noong bata ako" in {_words(o) for o in result.listed_reachable}
    assert "mula pa noong bata ako" not in {_words(c) for c in result.candidates}

    bare = report(exercise.model_copy(update={"accepted_orders": []}), split=True)
    assert "mula pa noong bata ako" in {_words(c) for c in bare.candidates}
    assert bare.total_unlisted == result.total_unlisted + 1


def test_phrase_movement_is_opt_in():
    exercise = _token(ex.L2_EX3)
    assert report(exercise).total_unlisted == 0

    phrased = report(exercise.model_copy(update={"accepted_orders": []}), phrases=True)
    assert "napunta ang leeg at pakpak ng manok kay padre damaso" in {_words(c) for c in phrased.candidates}

    kept = report(exercise, phrases=True)
    assert len(kept.listed_reachable) == 2 and kept.unreachable_listed == []


def test_block_and_split_counts_are_pinned():
    exercise = _token(ex.L5_EX4)
    assert report(exercise).total_unlisted == 28  # "From then on" moves as one block
    split = report(exercise, cap=10, split=True)
    assert split.total_unlisted == 1678
    assert len(split.candidates) == 10


def test_closed_form_is_exact_in_split_mode():
    exercise = _token(ex.L1_EX5)
    movers = frozenset({"sa", "po"})
    enumerated = set(iter_candidates(exercise, movers, split=True))
    assert candidate_count(exercise, movers, split=True) == len(enumerated) == 8 * 7 * 6 // 2
    assert report(exercise, movers, split=True).count_exact


def test_closed_form_is_an_upper_bound_in_block_mode(monkeypatch):
    probe = _token(ex.BLOCK_OVERCOUNT_PROBE)
    movers = frozenset({"na"})
    assert candidate_count(probe, movers) == 6
    assert len(set(iter_candidates(probe, movers))) == 4
    assert not report(probe, movers).count_exact

    monkeypatch.setattr(orders, "ENUMERATION_LIMIT", 1)
    assert "up to 6 orders" in format_report(report(probe, movers))


@pytest.mark.parametrize("data", [ex.L2_EX6, ex.L4_EX8], ids=["L2 ex6", "L4 ex8"])
def test_flags_are_additive(data):
    exercise = _token(data)
    everything = _folded(exercise, split=True, bank=True, phrases=True)
    assert _folded(exercise, split=True) <= everything
    assert _folded(exercise, phrases=True) <= everything
    assert _folded(exercise, bank=True) <= everything
    assert _folded(exercise) <= everything


def test_all_flags_still_reach_what_split_reaches():
    result = report(_token(ex.L2_EX6), split=True, bank=True, phrases=True)
    assert "mula pa noong bata ako" in {_words(o) for o in result.listed_reachable}


def test_bank_particle_moves_on_its_own_in_block_mode():
    probe = _token(ex.BANK_PROBE)
    candidates = {_words(c) for c in report(probe, bank=True).candidates}
    assert "umalis na po siya" in candidates
    assert "po umalis na siya" in candidates


def test_listed_orders_are_reported_above_the_limit(monkeypatch):
    monkeypatch.setattr(orders, "ENUMERATION_LIMIT", 100)
    town = report(_token(ex.L5_EX4), split=True)
    assert town.too_many and town.candidates == [] and town.total == 1680
    assert len(town.listed_reachable) == 1

    monkeypatch.setattr(orders, "ENUMERATION_LIMIT", 0)
    dinner = report(_token(ex.L2_EX3))
    assert dinner.too_many
    assert len(dinner.unreachable_listed) == 2
    text = format_report(dinner)
    assert "not reachable by mover rule" in text and "above the 0 limit" in text


def test_english_movers_for_tl_to_en():
    assert movers_for(_token(ex.L5_EX4)) == DEFAULT_EN_MOVERS  # tl_to_en
    assert movers_for(_token(ex.L5_EX8)) == DEFAULT_TL_MOVERS  # en_to_tl
    assert movers_for(_token(ex.L5_EX2)) == DEFAULT_TL_MOVERS  # sentence_assembly
    assert movers_for(_token(ex.L5_EX4), "Then, ON") == frozenset({"then", "on"})


def test_clitics_override_is_case_insensitive_and_keeps_tile_casing(tmp_path, capsys):
    exercise = _token(ex.L1_EX7).model_copy(update={"accepted_orders": []})
    shown = {" ".join(c) for c in report(exercise, movers=movers_for(exercise, "BUKAS")).candidates}
    assert "ay aalis ako patungong San Diego Bukas" in shown

    path = _lesson_file(tmp_path, ex.L1_EX7)
    assert main(["orders", str(path), "--key", "ex7", "--clitics", "BUKAS"]) == 0
    out = capsys.readouterr().out
    assert "Bukas" in out and "San Diego" in out


def test_cli_cap_and_counts(tmp_path, capsys):
    path = _lesson_file(tmp_path, ex.L5_EX4)
    assert main(["orders", str(path), "--key", "ex4", "--max", "10", "--split"]) == 0
    assert "showing 10 of 1678" in capsys.readouterr().out
    assert main(["orders", str(path), "--key", "ex4", "--max", "10"]) == 0
    assert "showing 10 of 28" in capsys.readouterr().out


def test_cli_skips_listen_tap_unless_asked(tmp_path, capsys):
    path = _lesson_file(tmp_path, ex.L2_EX4, ex.L5_EX2, ex.L5_EX1)
    assert main(["orders", str(path)]) == 0
    out = capsys.readouterr().out
    assert "ex4 listen_tap: skipped" in out
    assert "candidates" in out and "ex2 sentence_assembly" in out
    assert "ex1 " not in out  # comprehension_mc is never listed

    assert main(["orders", str(path), "--include-listen-tap"]) == 0
    assert "ex4 listen_tap\n" in capsys.readouterr().out


def test_cli_unknown_key_exits_non_zero(tmp_path):
    path = _lesson_file(tmp_path, ex.L5_EX2)
    with pytest.raises(SystemExit) as raised:
        main(["orders", str(path), "--key", "ex99"])
    assert raised.value.code not in (0, None)


def test_cli_multiple_choice_key_says_so(tmp_path):
    path = _lesson_file(tmp_path, ex.L5_EX1)
    with pytest.raises(SystemExit) as raised:
        main(["orders", str(path), "--key", "ex1"])
    assert "multiple choice" in str(raised.value.code)


def test_cli_rejects_a_negative_max(tmp_path):
    path = _lesson_file(tmp_path, ex.L5_EX2)
    with pytest.raises(SystemExit) as raised:
        main(["orders", str(path), "--max", "-1"])
    assert raised.value.code == 2  # argparse usage error


def test_cli_reports_bad_files_in_one_line(tmp_path):
    with pytest.raises(SystemExit) as missing:
        main(["orders", str(tmp_path / "nope.yaml")])
    assert "cannot read" in str(missing.value.code)

    unit = tmp_path / "unit.yaml"
    unit.write_text("slug: u\ntitle: U\norder_index: 1\nlessons: [a.yaml]\n", encoding="utf-8")
    with pytest.raises(SystemExit) as not_lesson:
        main(["orders", str(unit)])
    assert "not a valid lesson" in str(not_lesson.value.code)


def test_cli_runs_over_a_real_lesson():
    assert main(["orders", str(REAL_LESSON)]) == 0
