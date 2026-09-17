"""Behaviors for the pure progress rules (SPEC.md 6.5):
- streak increments when the last activity was yesterday in the learner's
  timezone, stays when it was today, resets to 1 when older or never
- hearts regenerate one per four hours up to five, computed on read, and
  the timestamp only advances by whole intervals so partial progress is
  kept
- the local date is computed in the learner's IANA timezone
"""

from datetime import UTC, date, datetime, timedelta

import pytest

from rizalai.progress.rules import HEART_INTERVAL, MAX_HEARTS, local_today, next_streak, regenerated_hearts

TODAY = date(2026, 9, 17)


@pytest.mark.parametrize(
    ("current", "last", "expected"),
    [
        (0, None, 1),
        (3, TODAY - timedelta(days=1), 4),
        (3, TODAY, 3),
        (3, TODAY - timedelta(days=2), 1),
        (7, TODAY - timedelta(days=30), 1),
    ],
)
def test_next_streak(current, last, expected):
    assert next_streak(current, last, TODAY) == expected


def test_hearts_regen_one_per_interval_capped():
    t0 = datetime(2026, 9, 17, 8, 0, tzinfo=UTC)
    assert regenerated_hearts(3, t0, t0 + timedelta(hours=3, minutes=59)) == (3, t0)
    assert regenerated_hearts(3, t0, t0 + HEART_INTERVAL) == (4, t0 + HEART_INTERVAL)
    hearts, stamp = regenerated_hearts(3, t0, t0 + timedelta(hours=9))
    assert hearts == MAX_HEARTS
    assert stamp == t0 + timedelta(hours=9)  # full: clock restarts now


def test_hearts_regen_keeps_partial_progress():
    t0 = datetime(2026, 9, 17, 8, 0, tzinfo=UTC)
    hearts, stamp = regenerated_hearts(2, t0, t0 + timedelta(hours=5))
    assert hearts == 3
    assert stamp == t0 + timedelta(hours=4)  # one hour toward the next heart is preserved


def test_full_hearts_do_not_drift_the_clock():
    t0 = datetime(2026, 9, 17, 8, 0, tzinfo=UTC)
    now = t0 + timedelta(days=3)
    assert regenerated_hearts(MAX_HEARTS, t0, now) == (MAX_HEARTS, now)


def test_local_today_uses_learner_timezone():
    # 23:30 UTC on the 16th is already the 17th in Manila (UTC+8).
    now = datetime(2026, 9, 16, 23, 30, tzinfo=UTC)
    assert local_today("Asia/Manila", now) == date(2026, 9, 17)
    assert local_today("UTC", now) == date(2026, 9, 16)
    assert local_today("Not/AZone", now) == date(2026, 9, 16)  # falls back to UTC
