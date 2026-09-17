"""TTS engines. Each adapter is optional: it is offered by available_engines
only when its dependency imports and its credentials exist. Nothing here
runs in the request path; audio is rendered once at seed time.

Candidates for the bake-off (docs/architecture.md D12):
- mms: Meta MMS-TTS, the only open model with a native Tagalog voice
  (facebook/mms-tts-tgl). Needs transformers and torch.
- xtts: Coqui XTTS v2. Open, multilingual, voice cloning from a reference
  clip, but Tagalog is not in its supported language list; it is included
  so the owner can hear the gap. Needs the TTS package and a reference wav.
- google: Google Cloud Text-to-Speech fil-PH Neural2 voices. Needs
  google-cloud-texttospeech and application default credentials.
"""

import hashlib
import io
import logging
import math
import os
import wave
from dataclasses import dataclass
from typing import Any, Protocol

from rizalai.config import Settings

log = logging.getLogger(__name__)


class TTSEngine(Protocol):
    name: str
    voice: str
    extension: str
    content_type: str

    def synthesize(self, text: str) -> bytes: ...


@dataclass
class FakeTTS:
    """A deterministic tone burst per text, valid WAV, no dependencies."""

    name: str = "fake"
    voice: str = "default"
    extension: str = "wav"
    content_type: str = "audio/wav"

    def synthesize(self, text: str) -> bytes:
        seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:4], "big")
        rate = 8000
        freq = 220 + seed % 440
        frames = bytearray()
        for i in range(rate // 4):
            sample = int(12000 * math.sin(2 * math.pi * freq * i / rate))
            frames += sample.to_bytes(2, "little", signed=True)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(bytes(frames))
        return buf.getvalue()


class MMSTTS:
    name = "mms"
    voice = "tgl"
    extension = "wav"
    content_type = "audio/wav"

    def __init__(self, model_id: str = "facebook/mms-tts-tgl") -> None:
        import torch  # type: ignore[import-not-found]
        from transformers import AutoTokenizer, VitsModel  # type: ignore[import-not-found]

        self._torch = torch
        self._model = VitsModel.from_pretrained(model_id)
        self._tokenizer = AutoTokenizer.from_pretrained(model_id)

    def synthesize(self, text: str) -> bytes:
        inputs = self._tokenizer(text, return_tensors="pt")
        with self._torch.no_grad():
            waveform = self._model(**inputs).waveform[0].numpy()
        rate = int(self._model.config.sampling_rate)
        pcm = (waveform * 32767).clip(-32768, 32767).astype("int16").tobytes()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(pcm)
        return buf.getvalue()


class XTTS:
    name = "xtts"
    voice = "reference"
    extension = "wav"
    content_type = "audio/wav"

    def __init__(self, speaker_wav: str, language: str = "en") -> None:
        from TTS.api import TTS  # type: ignore[import-not-found]

        self._tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        self._speaker_wav = speaker_wav
        self._language = language

    def synthesize(self, text: str) -> bytes:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            self._tts.tts_to_file(
                text=text, speaker_wav=self._speaker_wav, language=self._language, file_path=tmp.name
            )
            tmp.seek(0)
            return tmp.read()


class GoogleTTS:
    name = "google"
    voice = "fil-PH-Neural2-A"
    extension = "mp3"
    content_type = "audio/mpeg"

    def __init__(self, voice: str = "fil-PH-Neural2-A") -> None:
        from google.cloud import texttospeech  # type: ignore[import-not-found]

        self._tts: Any = texttospeech
        self._client = texttospeech.TextToSpeechClient()
        self.voice = voice

    def synthesize(self, text: str) -> bytes:
        tts = self._tts
        response = self._client.synthesize_speech(
            input=tts.SynthesisInput(text=text),
            voice=tts.VoiceSelectionParams(language_code="fil-PH", name=self.voice),
            audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3),
        )
        return bytes(response.audio_content)


def available_engines(settings: Settings | None) -> list[TTSEngine]:
    """Every engine that can be constructed right now. Fake is always there."""
    engines: list[TTSEngine] = [FakeTTS()]
    try:
        engines.append(MMSTTS())
    except Exception as exc:  # noqa: BLE001 - optional dependency or download failure
        log.info("mms engine unavailable: %s", exc)
    speaker = settings.xtts_speaker_wav if settings else ""
    if speaker and os.path.exists(speaker):
        try:
            engines.append(XTTS(speaker))
        except Exception as exc:  # noqa: BLE001
            log.info("xtts engine unavailable: %s", exc)
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            engines.append(GoogleTTS())
        except Exception as exc:  # noqa: BLE001
            log.info("google engine unavailable: %s", exc)
    return engines


def engine_by_name(name: str, settings: Settings | None) -> TTSEngine:
    for engine in available_engines(settings):
        if engine.name == name:
            return engine
    raise ValueError(
        f"TTS engine {name!r} is not available; installed: {[e.name for e in available_engines(settings)]}"
    )
