"""Load and validate content YAML.

Layout:
  content/units/<folder>/unit.yaml      unit metadata and ordered lesson files
  content/units/<folder>/<lesson>.yaml  one LessonContent each

Ids are uuid5 of slugs so that re-seeding is idempotent and progress rows
keep pointing at the same exercises.
"""

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from rizalai.contracts.lesson import LessonContent

NAMESPACE = uuid.UUID("6f1c2b8e-9c1a-4c3e-8f2d-1a2b3c4d5e6f")


class UnitFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=80)
    title: str = Field(min_length=1, max_length=160)
    order_index: int = Field(ge=0)
    lessons: list[str] = Field(min_length=1)


class UnitContent(BaseModel):
    slug: str
    title: str
    order_index: int
    lessons: list[LessonContent]


def unit_id(slug: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"unit:{slug}")


def lesson_id(slug: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"lesson:{slug}")


def exercise_id(lesson_slug: str, key: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"exercise:{lesson_slug}:{key}")


def content_hash(lesson: LessonContent) -> str:
    canonical = json.dumps(lesson.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _read_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_lesson(path: Path) -> LessonContent:
    """One lesson file, validated through the contract."""
    return LessonContent.model_validate(_read_yaml(path))


def load_content(content_dir: Path) -> list[UnitContent]:
    units_dir = content_dir / "units"
    if not units_dir.is_dir():
        raise FileNotFoundError(f"no units directory at {units_dir}")

    units: list[UnitContent] = []
    for folder in sorted(p for p in units_dir.iterdir() if p.is_dir()):
        unit_file = folder / "unit.yaml"
        if not unit_file.exists():
            continue
        unit = UnitFile.model_validate(_read_yaml(unit_file))
        lessons = [LessonContent.model_validate(_read_yaml(folder / name)) for name in unit.lessons]
        slugs = [lesson.slug for lesson in lessons]
        if len(slugs) != len(set(slugs)):
            raise ValueError(f"duplicate lesson slugs in unit {unit.slug}")
        units.append(
            UnitContent(
                slug=unit.slug,
                title=unit.title,
                order_index=unit.order_index,
                lessons=lessons,
            )
        )
    units.sort(key=lambda u: u.order_index)
    return units
