"""Enumerate the word orders a token exercise's tiles can build (plan 006).

Reviewers must list every natural spoken order in accepted_orders (D34), and
must make sure no distractor completes an unlisted one. Naturalness stays a
human judgment; this module only enumerates what the tiles can build, so the
reviewer reads a short list instead of permuting in their head.

The rule: the primary order (answer_tokens) is cut into units. Movers are
particles and pronouns that shift position in speech (po, ba, na, pa, ako,
bukas and so on; function words for English targets). In the default block
mode each maximal run of adjacent movers is one unit ("From then on"); split
mode moves every mover on its own. Non-mover units keep their relative
order, and movable units take every choice of positions and every distinct
arrangement. Two opt-ins widen the net:

- bank: also try the primary with one of ay, pa, po, ba dropped, with one
  mover swapped for a bank-only mover, and with one bank-only mover added; a
  particle brought in from the bank is always its own unit, so it moves on
  its own even in block mode;
- phrases: also cut into phrases (a marker such as ang, kay or sa plus the
  content words after it, the leading predicate, or a mover) and permute
  them all.

Flags are additive: the result is the union of every cut the flags ask for
(block, or split with --split, plus phrases with --phrases) over every bank
variant, so turning a flag on never loses an order another flag reaches.
Split mode reaches every block-mode order, so --split replaces block rather
than adding to it.

Candidates are compared case-insensitively (grading folds case), shown with
the tiles' own casing, deduplicated, and sorted so the smallest changes come
first. Whether an authored order is reachable is checked against the unit
rule directly, so it is reported even when there are too many orders to
list. Anything above ENUMERATION_LIMIT is counted, not listed.
"""

from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from itertools import combinations
from math import factorial, prod

from rizalai.contracts.lesson import TokenExercise, TranslateLine

DEFAULT_TL_MOVERS = frozenset(
    {
        "po", "ho", "ba", "na", "pa", "nang", "ay", "kaya", "lang", "lamang", "din", "rin", "daw", "raw",
        "nga", "naman", "pala", "yata", "muna", "sana", "ko", "mo", "ka", "ako", "siya", "kita", "kayo",
        "ito", "iyon", "doon", "dito", "diyan", "bukas", "ngayon", "kami", "tayo", "sila", "niya", "nila",
        "n'yo", "akong", "kang", "siyang",
    }
)  # fmt: skip
DEFAULT_EN_MOVERS = frozenset({"the", "a", "an", "on", "from", "to", "of", "then", "now", "up"})

# Words that open a phrase unit in phrases mode.
TL_MARKERS = frozenset({"ang", "kay", "sa", "si", "ni", "sina", "nina", "kina", "mga"})
EN_MARKERS = frozenset({"in", "at", "for", "with", "by", "near", "into", "through", "over"})

# Particles the bank opt-in may drop from the primary.
DROPPABLE = frozenset({"ay", "pa", "po", "ba"})

ENUMERATION_LIMIT = 50_000

Unit = tuple[str, ...]
Order = tuple[str, ...]


def _fold(tokens: Iterable[str]) -> Order:
    return tuple(t.lower() for t in tokens)


def _english(ex: TokenExercise) -> bool:
    return isinstance(ex, TranslateLine) and ex.direction == "tl_to_en"


def movers_for(ex: TokenExercise, override: str | None = None) -> frozenset[str]:
    """The mover list for an exercise: an explicit comma-separated override
    (any letter case), else English movers for tl_to_en, else Tagalog."""
    if override is not None:
        return frozenset(m.strip().lower() for m in override.split(",") if m.strip())
    return DEFAULT_EN_MOVERS if _english(ex) else DEFAULT_TL_MOVERS


Cut = str  # "block", "split" or "phrases"


def _units(
    tokens: Sequence[str],
    movers: frozenset[str],
    *,
    cut: Cut,
    split: bool,
    english: bool,
    solo: frozenset[int] = frozenset(),
) -> "Plan":
    """Cut tokens into units and mark which may move. Tokens at the indices
    in `solo` (particles brought in from the bank) are set aside: they are
    inserted afterwards at every token position, so they can land anywhere,
    even inside a block of movers."""
    phrases = cut == "phrases"
    join_movers = not split and cut != "split"
    units: list[Unit] = []
    movable: list[bool] = []
    solos: list[str] = []
    markers = EN_MARKERS if english else TL_MARKERS
    current: list[str] = []
    current_kind = ""  # "mover", "solo", "phrase" or "fixed"

    def close() -> None:
        nonlocal current, current_kind
        if current:
            units.append(tuple(current))
            movable.append(phrases or current_kind == "mover")
        current, current_kind = [], ""

    for i, token in enumerate(tokens):
        low = token.lower()
        if i in solo:
            solos.append(token)
        elif low in movers:
            if current_kind == "mover" and join_movers:
                current.append(token)
            else:
                close()
                current, current_kind = [token], "mover"
        elif phrases and low in markers:
            close()
            current, current_kind = [token], "phrase"
        elif phrases and current_kind == "phrase":
            current.append(token)
        elif phrases:
            close()
            current, current_kind = [token], "phrase"
        else:
            close()
            current, current_kind = [token], "fixed"
    close()
    return Plan(units, movable, solos)


@dataclass
class Plan:
    """One way to cut an order: units (movable or not) plus bank particles
    that may be inserted at any token position."""

    units: list[Unit]
    movable: list[bool]
    solos: list[str] = field(default_factory=list)


def _count_plan(plan: Plan) -> int:
    base = _count_units(plan.units, plan.movable)
    length = sum(len(u) for u in plan.units)
    s = len(plan.solos)
    repeats = prod(factorial(c) for c in Counter(t.lower() for t in plan.solos).values())
    return base * factorial(length + s) // factorial(length) // repeats


def _insertions(order: Order, solos: list[str]) -> Iterator[Order]:
    """`order` with the solo tokens inserted at every choice of positions."""
    if not solos:
        yield order
        return
    total = len(order) + len(solos)
    for slots in combinations(range(total), len(solos)):
        for perm in _distinct_permutations([(t,) for t in solos]):
            placed = dict(zip(slots, perm, strict=True))
            rest = iter(order)
            yield tuple(placed[i][0] if i in placed else next(rest) for i in range(total))


def _plan_orders(plan: Plan) -> Iterator[Order]:
    for base in _arrangements(plan.units, plan.movable):
        yield from _insertions(base, plan.solos)


def _count_units(units: list[Unit], movable: list[bool]) -> int:
    n = len(units)
    moving = Counter(_fold(u) for u, m in zip(units, movable, strict=True) if m)
    k = sum(moving.values())
    return factorial(n) // factorial(n - k) // prod(factorial(c) for c in moving.values())


def _distinct_permutations(items: list[Unit]) -> Iterator[tuple[Unit, ...]]:
    """Permutations of a multiset, each distinct arrangement once (folded)."""
    groups: dict[Order, list[Unit]] = {}
    for item in items:
        groups.setdefault(_fold(item), []).append(item)
    keys = list(groups)
    counts = [len(groups[k]) for k in keys]
    arrangement: list[Unit] = []

    def walk() -> Iterator[tuple[Unit, ...]]:
        if len(arrangement) == len(items):
            yield tuple(arrangement)
            return
        for i, key in enumerate(keys):
            if counts[i]:
                counts[i] -= 1
                arrangement.append(groups[key][counts[i]])
                yield from walk()
                arrangement.pop()
                counts[i] += 1

    yield from walk()


def _arrangements(units: list[Unit], movable: list[bool]) -> Iterator[Order]:
    n = len(units)
    fixed = [u for u, m in zip(units, movable, strict=True) if not m]
    moving = [u for u, m in zip(units, movable, strict=True) if m]
    for slots in combinations(range(n), len(moving)):
        for perm in _distinct_permutations(moving):
            placed = dict(zip(slots, perm, strict=True))
            rest = iter(fixed)
            yield tuple(tok for i in range(n) for tok in (placed[i] if i in placed else next(rest)))


def _variants(
    ex: TokenExercise, movers: frozenset[str], bank: bool
) -> list[tuple[list[str], frozenset[int]]]:
    """The primary, plus with bank the drop, swap and add variants, each with
    the indices of the particles that came from the bank."""
    primary = list(ex.answer_tokens)
    variants: list[tuple[list[str], frozenset[int]]] = [(primary, frozenset())]
    if not bank:
        return variants
    spare = Counter(ex.bank) - Counter(primary)
    extra = sorted({t for t in spare if t.lower() in movers})
    for i, tok in enumerate(primary):
        if tok.lower() in DROPPABLE:
            variants.append((primary[:i] + primary[i + 1 :], frozenset()))
        if tok.lower() in movers:
            variants.extend((primary[:i] + [e] + primary[i + 1 :], frozenset({i})) for e in extra)
    variants.extend((primary + [e], frozenset({len(primary)})) for e in extra)
    return variants


def _cuts(split: bool, phrases: bool) -> list[Cut]:
    return (["split"] if split else ["block"]) + (["phrases"] if phrases else [])


def _plans(
    ex: TokenExercise, movers: frozenset[str], *, split: bool, bank: bool, phrases: bool
) -> list[Plan]:
    english = _english(ex)
    return [
        _units(tokens, movers, cut=cut, split=split, english=english, solo=solo)
        for tokens, solo in _variants(ex, movers, bank)
        for cut in _cuts(split, phrases)
    ]


def count_is_exact(*, split: bool, bank: bool, phrases: bool) -> bool:
    """The closed form is exact only for one split cut of the primary: in
    block mode, arrangements of multi-token blocks can join into the same
    order, and with bank or phrases several plans overlap."""
    return split and not bank and not phrases


def candidate_count(
    ex: TokenExercise,
    movers: frozenset[str],
    *,
    split: bool = False,
    bank: bool = False,
    phrases: bool = False,
) -> int:
    """Closed-form number of orders the rule builds, the primary included:
    n! / ((n - k)! * prod(m_i!)) for n units of which k move, m_i copies of
    each distinct moving unit, summed over the plans. Exact in split mode
    without bank or phrases (count_is_exact); otherwise an upper bound."""
    return sum(_count_plan(p) for p in _plans(ex, movers, split=split, bank=bank, phrases=phrases))


def iter_candidates(
    ex: TokenExercise,
    movers: frozenset[str],
    *,
    split: bool = False,
    bank: bool = False,
    phrases: bool = False,
) -> Iterator[Order]:
    """Every distinct order (folded), the primary included, in tile casing:
    the union over every plan the flags ask for."""
    seen: set[Order] = set()
    for plan in _plans(ex, movers, split=split, bank=bank, phrases=phrases):
        for order in _plan_orders(plan):
            key = _fold(order)
            if key not in seen:
                seen.add(key)
                yield order


def _buildable(order: Order, plan: Plan) -> bool:
    """Whether one plan can build `order`, without enumerating: take out the
    bank particles at every matching position, then match the rest against
    the units (fixed ones in their order, movable ones once each, anywhere)."""
    folded = _fold(order)
    solos = sorted(t.lower() for t in plan.solos)
    if not solos:
        return _units_build(folded, plan.units, plan.movable)
    for picked in combinations(range(len(folded)), len(solos)):
        if sorted(folded[i] for i in picked) == solos:
            rest = tuple(t for i, t in enumerate(folded) if i not in picked)
            if _units_build(rest, plan.units, plan.movable):
                return True
    return False


def _units_build(target: Order, units: list[Unit], movable: list[bool]) -> bool:
    fixed = [_fold(u) for u, m in zip(units, movable, strict=True) if not m]
    moving = Counter(_fold(u) for u, m in zip(units, movable, strict=True) if m)
    memo: dict[tuple[int, int, tuple[tuple[Order, int], ...]], bool] = {}

    def fits(pos: int, unit: Order) -> bool:
        return target[pos : pos + len(unit)] == unit

    def walk(pos: int, next_fixed: int, left: Counter[Order]) -> bool:
        state = (pos, next_fixed, tuple(sorted(left.items())))
        if state in memo:
            return memo[state]
        if pos == len(target):
            done = next_fixed == len(fixed) and not +left
            memo[state] = done
            return done
        found = False
        if next_fixed < len(fixed) and fits(pos, fixed[next_fixed]):
            found = walk(pos + len(fixed[next_fixed]), next_fixed + 1, left)
        for unit, count in list(left.items()):
            if found:
                break
            if count and fits(pos, unit):
                left[unit] -= 1
                found = walk(pos + len(unit), next_fixed, left)
                left[unit] += 1
        memo[state] = found
        return found

    return walk(0, 0, moving)


def _displacement(order: Order, primary: Order) -> tuple[int, int, Order]:
    """Sort key: tokens out of their primary slot, then Kendall distance of
    the greedy match against the primary, then the words themselves."""
    folded, target = _fold(order), _fold(primary)
    moved = sum(1 for i, t in enumerate(folded) if i >= len(target) or target[i] != t) + abs(
        len(folded) - len(target)
    )
    free: dict[str, list[int]] = {}
    for i, t in enumerate(target):
        free.setdefault(t, []).append(i)
    ranks = [free[t].pop(0) if free.get(t) else len(target) for t in folded]
    inversions = sum(1 for a, b in combinations(ranks, 2) if a > b)
    return moved, inversions, folded


@dataclass
class OrdersReport:
    key: str
    type: str
    direction: str | None
    primary: Order
    listed: list[Order]
    listed_reachable: list[Order] = field(default_factory=list)
    unreachable_listed: list[Order] = field(default_factory=list)
    candidates: list[Order] = field(default_factory=list)
    total: int = 0
    total_unlisted: int = 0
    cap: int = 50
    too_many: bool = False
    count_exact: bool = True


def report(
    ex: TokenExercise,
    movers: frozenset[str] | None = None,
    cap: int = 50,
    *,
    split: bool = False,
    bank: bool = False,
    phrases: bool = False,
) -> OrdersReport:
    movers = movers if movers is not None else movers_for(ex)
    primary: Order = tuple(ex.answer_tokens)
    listed = [tuple(o) for o in ex.accepted_orders]
    plans = _plans(ex, movers, split=split, bank=bank, phrases=phrases)
    reachable = [o for o in listed if any(_buildable(o, plan) for plan in plans)]
    result = OrdersReport(
        key=ex.key,
        type=str(ex.model_dump(include={"type"})["type"]),
        direction=getattr(ex, "direction", None),
        primary=primary,
        listed=listed,
        listed_reachable=reachable,
        unreachable_listed=[o for o in listed if o not in reachable],
        cap=cap,
        count_exact=count_is_exact(split=split, bank=bank, phrases=phrases),
    )
    total = candidate_count(ex, movers, split=split, bank=bank, phrases=phrases)
    if total > ENUMERATION_LIMIT:
        result.total, result.too_many = total, True
        return result

    orders = list(iter_candidates(ex, movers, split=split, bank=bank, phrases=phrases))
    result.total = len(orders)
    exclude = {_fold(primary)} | {_fold(o) for o in listed}
    unlisted = sorted((o for o in orders if _fold(o) not in exclude), key=lambda o: _displacement(o, primary))
    result.total_unlisted = len(unlisted)
    result.candidates = unlisted[:cap]
    return result


def format_report(r: OrdersReport) -> str:
    """The CLI text for one exercise, tile casing kept."""
    words = " ".join
    head = f"{r.key} {r.type}" + (f" ({r.direction})" if r.direction else "")
    lines = [head, f"  primary: {words(r.primary)}"]
    lines += [f"  listed: {words(o)}" for o in r.listed_reachable]
    lines += [f"  not reachable by mover rule: {words(o)}" for o in r.unreachable_listed]
    if r.too_many:
        size = f"{r.total}" if r.count_exact else f"up to {r.total}"
        lines.append(f"  candidates: {size} orders, above the {ENUMERATION_LIMIT} limit; not listed")
        return "\n".join(lines)
    lines.append(f"  candidates (showing {len(r.candidates)} of {r.total_unlisted} unlisted, cap {r.cap}):")
    lines += [f"    {words(o)}" for o in r.candidates]
    return "\n".join(lines)
