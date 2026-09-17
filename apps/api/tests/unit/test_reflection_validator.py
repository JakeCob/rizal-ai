"""Behavior (DECISIONS.md D03): every quoted span in a reflection must be a
verbatim substring of the passage it cites. Whitespace differences are
tolerated, nothing else. An unknown passage id is a failure."""

import uuid

from rizalai.generation.schema import QuotedSpan, ReflectionDraft
from rizalai.generation.validator import validate_citations

P1 = uuid.uuid4()
P2 = uuid.uuid4()
PASSAGES = {
    P1: (
        "A fines de Octubre, don Santiago de los Santos, conocido popularmente "
        "con el nombre de «Capitán Tiago», daba una cena."
    ),
    P2: "Nag-anyaya n~g pagpapacain nang isáng hapunan, n~g magtátapos ang Octubre.",
}


def _draft(*spans: QuotedSpan) -> ReflectionDraft:
    return ReflectionDraft(tl="Isang hapunan.", en="A dinner.", quoted_spans=list(spans))


def test_verbatim_span_passes():
    draft = _draft(QuotedSpan(text="daba una cena", passage_id=P1))
    assert validate_citations(draft, PASSAGES) == []


def test_whitespace_differences_are_tolerated():
    draft = _draft(QuotedSpan(text="don  Santiago de los\nSantos", passage_id=P1))
    assert validate_citations(draft, PASSAGES) == []


def test_paraphrase_fails():
    draft = _draft(QuotedSpan(text="Capitán Tiago gave a dinner", passage_id=P1))
    errors = validate_citations(draft, PASSAGES)
    assert len(errors) == 1 and "not a verbatim substring" in errors[0]


def test_unknown_passage_fails():
    draft = _draft(QuotedSpan(text="daba una cena", passage_id=uuid.uuid4()))
    errors = validate_citations(draft, PASSAGES)
    assert len(errors) == 1 and "unknown passage" in errors[0]


def test_case_change_fails():
    draft = _draft(QuotedSpan(text="Daba Una Cena", passage_id=P1))
    assert validate_citations(draft, PASSAGES)


def test_no_spans_is_valid():
    assert validate_citations(_draft(), PASSAGES) == []


def test_multiple_spans_report_each_failure():
    draft = _draft(
        QuotedSpan(text="daba una cena", passage_id=P1),
        QuotedSpan(text="invented words", passage_id=P2),
        QuotedSpan(text="isáng hapunan", passage_id=P2),
    )
    errors = validate_citations(draft, PASSAGES)
    assert len(errors) == 1
