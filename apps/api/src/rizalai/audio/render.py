"""Render lines to a store, keyed by content hash, and the bake-off."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from rizalai.audio.engines import TTSEngine
from rizalai.audio.store import AudioStore


def audio_key(engine: str, voice: str, text: str, ext: str = "wav") -> str:
    digest = hashlib.sha256(f"{engine}|{voice}|{text}".encode()).hexdigest()[:16]
    return f"{digest}.{ext}"


def key_for(engine: TTSEngine, text: str) -> str:
    return audio_key(engine.name, engine.voice, text, engine.extension)


@dataclass
class RenderReport:
    rendered: int = 0
    skipped: int = 0


def render_lines(lines: list[str], engine: TTSEngine, store: AudioStore) -> RenderReport:
    report = RenderReport()
    seen: set[str] = set()
    for text in lines:
        key = key_for(engine, text)
        if key in seen or store.exists(key):
            report.skipped += 1
            seen.add(key)
            continue
        store.put(key, engine.synthesize(text), engine.content_type)
        seen.add(key)
        report.rendered += 1
    return report


def bakeoff(lines: list[str], engines: list[TTSEngine], out_dir: Path) -> list[Path]:
    """One file per engine per line, named for listening side by side."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for engine in engines:
        for i, text in enumerate(lines, start=1):
            path = out_dir / f"{engine.name}-{i:02d}.{engine.extension}"
            path.write_bytes(engine.synthesize(text))
            written.append(path)
    return written
