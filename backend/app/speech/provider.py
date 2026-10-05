"""Speech-to-text behind a provider interface. faster-whisper is the self-hosted default."""

import io
import logging
import threading
from dataclasses import dataclass, field
from typing import Protocol

import av
import numpy as np

from app.core.config import get_settings

SAMPLE_RATE = 16_000

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Transcript:
    text: str
    provider: str
    model: str
    duration_s: float
    no_speech_prob: float
    avg_logprob: float | None
    # Words the recogniser was unsure about; shown to clinicians as uncertainty.
    low_confidence_words: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()


def decode_audio(audio: bytes) -> np.ndarray:
    """Decode any browser recording (webm/ogg/mp4/wav) to 16 kHz mono float32, in memory."""
    resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
    pcm: list[np.ndarray] = []
    with av.open(io.BytesIO(audio), mode="r") as container:
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame):
                pcm.append(out.to_ndarray().reshape(-1))
        for out in resampler.resample(None):
            pcm.append(out.to_ndarray().reshape(-1))
    if not pcm:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(pcm).astype(np.float32) / 32768.0


class SpeechProvider(Protocol):
    def transcribe(self, audio: bytes, language: str) -> Transcript: ...


class FasterWhisperProvider:
    """Settings chosen for aphasia: transcribe what was said, not what was likely meant.

    - no initial prompt and no conditioning on previous text (avoids "correcting" errors)
    - temperature 0 (deterministic), VAD to ignore silence
    - word probabilities kept so uncertain words can be flagged
    """

    name = "faster-whisper"
    LOW_CONFIDENCE = 0.5

    def __init__(self, model: str, device: str, compute_type: str) -> None:
        self.model_name = model
        self._args = (model, device, compute_type)
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                from faster_whisper import WhisperModel

                model, device, compute_type = self._args
                log.info("loading whisper model", extra={"data": {"model": model}})
                self._model = WhisperModel(model, device=device, compute_type=compute_type)
        return self._model

    def transcribe(self, audio: bytes, language: str) -> Transcript:
        segments, info = self._load().transcribe(
            decode_audio(audio),
            language=language,
            beam_size=5,
            temperature=0.0,
            condition_on_previous_text=False,
            initial_prompt=None,
            vad_filter=True,
            word_timestamps=True,
        )
        segments = list(segments)
        words = [w for s in segments for w in (s.words or [])]
        return Transcript(
            text=" ".join(s.text.strip() for s in segments).strip(),
            provider=self.name,
            model=self.model_name,
            duration_s=round(info.duration, 2),
            no_speech_prob=round(max((s.no_speech_prob for s in segments), default=1.0), 3),
            avg_logprob=round(sum(s.avg_logprob for s in segments) / len(segments), 3)
            if segments
            else None,
            low_confidence_words=[
                w.word.strip() for w in words if w.probability < self.LOW_CONFIDENCE
            ],
        )


_provider: SpeechProvider | None = None


def get_speech_provider() -> SpeechProvider:
    global _provider
    if _provider is None:
        s = get_settings()
        _provider = FasterWhisperProvider(s.whisper_model, s.whisper_device, s.whisper_compute_type)
    return _provider
