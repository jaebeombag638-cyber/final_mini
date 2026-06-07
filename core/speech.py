from collections.abc import Callable
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import config


@dataclass(frozen=True)
class SpeechRecognitionResult:
    """Stage 2에서 사용할 음성 인식 판정 결과를 담는다."""

    target_text: str
    recognized_text: str
    similarity: float
    passed: bool
    is_fallback: bool = False
    error_message: str | None = None


class SpeechRecognizer:
    """짧은 음성을 Whisper 결과와 목표 문장 유사도로 판정한다."""

    def __init__(
        self,
        target_text: str = config.SPEECH_TARGET_TEXT,
        pass_score: float = config.SPEECH_SIMILARITY_PASS,
        sample_rate: int = 16000,
        model_name: str = config.WHISPER_MODEL_NAME,
        model_dir: str = config.WHISPER_MODEL_DIR,
        recorder: Any | None = None,
        model: Any | None = None,
        model_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.target_text = target_text
        self.pass_score = pass_score
        self.sample_rate = sample_rate
        self.model_name = model_name
        self.model_dir = model_dir
        self.recorder = recorder or SoundDeviceRecorder()
        self.model = model
        self.model_factory = model_factory
        self._load_error_message: str | None = None

    def recognize(self, duration_seconds: float) -> SpeechRecognitionResult:
        try:
            samples = self.recorder.record(duration_seconds, self.sample_rate)
            recognized_text = self._get_model().transcribe(samples)
        except Exception as error:
            return SpeechRecognitionResult(
                target_text=self.target_text,
                recognized_text="",
                similarity=0.0,
                passed=False,
                is_fallback=True,
                error_message=str(error),
            )

        similarity = self.calculate_similarity(recognized_text)
        return SpeechRecognitionResult(
            target_text=self.target_text,
            recognized_text=recognized_text,
            similarity=similarity,
            passed=similarity >= self.pass_score,
        )

    def calculate_similarity(self, recognized_text: str) -> float:
        target = self._normalize_text(self.target_text)
        recognized = self._normalize_text(recognized_text)
        if not target or not recognized:
            return 0.0

        return round(SequenceMatcher(None, target, recognized).ratio(), 4)

    def release(self) -> None:
        if self.model is not None and hasattr(self.model, "close"):
            self.model.close()
        self.model = None

    def _get_model(self):
        if self.model is not None:
            return self.model

        try:
            factory = self.model_factory or self._create_default_model
            self.model = factory()
        except Exception as error:
            self._load_error_message = str(error)
            raise RuntimeError(self._load_error_message) from error

        return self.model

    def _create_default_model(self):
        return WhisperAdapter(self.model_name, self.model_dir)

    def _normalize_text(self, text: str) -> str:
        return "".join(str(text).lower().split())


class SoundDeviceRecorder:
    """sounddevice로 일정 시간 녹음한 mono float32 샘플을 반환한다."""

    def record(self, duration_seconds: float, sample_rate: int):
        sounddevice = self._import_sounddevice()
        frame_count = max(int(duration_seconds * sample_rate), 1)
        samples = sounddevice.rec(
            frame_count,
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        sounddevice.wait()
        return samples

    def _import_sounddevice(self):
        import sounddevice

        return sounddevice


class WhisperAdapter:
    """openai-whisper 호출부를 SpeechRecognizer에서 분리한다."""

    def __init__(self, model_name: str, model_dir: str = config.WHISPER_MODEL_DIR) -> None:
        whisper = self._import_whisper()
        model_path = Path(model_dir)
        model_path.mkdir(parents=True, exist_ok=True)
        self._model = whisper.load_model(model_name, download_root=str(model_path))

    def transcribe(self, samples) -> str:
        audio = self._prepare_audio(samples)
        result = self._model.transcribe(audio, fp16=False)
        return str(result.get("text", "")).strip()

    def _prepare_audio(self, samples):
        np = self._import_numpy()
        return np.asarray(samples, dtype=np.float32).reshape(-1)

    def _import_numpy(self):
        import numpy as np

        return np

    def _import_whisper(self):
        import whisper

        return whisper
