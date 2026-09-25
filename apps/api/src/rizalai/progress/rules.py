"""Pure progress rules (DECISIONS.md D16, D17). No database, no clock: the
caller passes `now`, which keeps these testable and the endpoints thin."""

from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rizalai.db.models import User

MAX_HEARTS = 5
HEART_INTERVAL = timedelta(hours=4)


def next_streak(current: int, last_activity: date | None, today: date) -> int:
    if last_activity is None:
        return 1
    if last_activity == today:
        return current
    if last_activity == today - timedelta(days=1):
        return current + 1
    return 1


def regenerated_hearts(hearts: int, updated_at: datetime, now: datetime) -> tuple[int, datetime]:
    """Lazy regeneration: one heart per interval since updated_at. The stamp
    advances only by whole intervals so partial progress toward the next
    heart is kept. At full hearts the clock simply restarts."""
    if hearts >= MAX_HEARTS:
        return MAX_HEARTS, now
    intervals = int((now - updated_at) // HEART_INTERVAL)
    if intervals <= 0:
        return hearts, updated_at
    regained = min(MAX_HEARTS, hearts + intervals)
    if regained >= MAX_HEARTS:
        return MAX_HEARTS, now
    return regained, updated_at + intervals * HEART_INTERVAL


def local_today(tz_name: str, now: datetime) -> date:
    try:
        zone = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")
    return now.astimezone(zone).date()


def is_valid_timezone(tz_name: str) -> bool:
    try:
        ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        return False
    return True


def apply_regen(user: User, now: datetime | None = None) -> bool:
    """Bring the user's hearts up to date in place. Returns True if changed."""
    now = now or datetime.now(UTC)
    hearts, stamp = regenerated_hearts(user.hearts, user.hearts_updated_at, now)
    changed = hearts != user.hearts or stamp != user.hearts_updated_at
    user.hearts = hearts
    user.hearts_updated_at = stamp
    return changed


def spend_heart(user: User, now: datetime) -> None:
    apply_regen(user, now)
    if user.hearts >= MAX_HEARTS:
        user.hearts_updated_at = now  # the regen clock starts when the first heart is lost
    user.hearts = max(0, user.hearts - 1)


def _token_list(value: Any) -> list[str] | None:
    if isinstance(value, list) and all(isinstance(t, str) for t in value):
        return [t.lower() for t in value]
    return None


def grade_response(exercise_type: str, answer: dict[str, Any], response: dict[str, Any]) -> bool:
    """Server-side grading, the mirror of lib/runner/grade.ts on the web
    (DECISIONS.md D34). A token answer is correct when the tapped tokens equal
    answer_tokens or any accepted order, compared after lowercasing every
    token. Rows seeded before accepted_orders existed grade on answer_tokens
    alone. Empty or malformed candidates are skipped and malformed taps grade
    wrong, never raising. comprehension_mc compares an int option index (a
    bool is not an index), matching the web's strict equality."""
    if exercise_type == "comprehension_mc":
        index = response.get("optionIndex")
        is_int = isinstance(index, int) and not isinstance(index, bool)
        return is_int and index == answer.get("correct_index")
    tokens = _token_list(response.get("tokens"))
    if tokens is None:
        return False
    orders = answer.get("accepted_orders")
    candidates = [answer.get("answer_tokens"), *(orders if isinstance(orders, list) else [])]
    return any(tokens == expected for expected in map(_token_list, candidates) if expected)
