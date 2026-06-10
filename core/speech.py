import numpy as np
import scipy.signal as signal
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
import config

@dataclass(frozen=True)
class SpeechRecognitionResult:
    target_text: str
    recognized_text: str
    similarity: float
    passed: bool
    is_fallback: bool = False
    error_message: str | None = None

class SpeechRecognizer:
    def __init__(
        self,
        target_text: str = config.SPEECH_TARGET_TEXT,
        pass_score: float = config.SPEECH_SIMILARITY_PASS,
        sample_rate: int = 16000,
        model_name: str = config.WHISPER_MODEL_NAME,
        model_dir: str = config.WHISPER_MODEL_DIR,
        model: Any | None = None,
    ) -> None:
        self.target_text = target_text
        self.pass_score = pass_score
        self.sample_rate = sample_rate
        self.model_name = model_name
        self.model_dir = model_dir
        self.model = model
        self._load_error_message: str | None = None

    def recognize_buffer(self, raw_audio, source_sample_rate=48000) -> SpeechRecognitionResult:
        try:
            # 1. 2채널 데이터를 1채널 모노 데이터로 평균 내어 압축
            if raw_audio.ndim > 1 and raw_audio.shape[1] == 2:
                mono_audio = np.mean(raw_audio, axis=1)
            else:
                mono_audio = raw_audio.flatten()

            # 2. Scipy를 사용해 48000Hz -> 16000Hz로 정밀 리샘플링 (테스트 성공 로직!)
            target_rate = 16000
            if source_sample_rate != target_rate:
                num_samples = int(len(mono_audio) * target_rate / source_sample_rate)
                final_audio = signal.resample(mono_audio, num_samples).astype(np.float32)
            else:
                final_audio = mono_audio.astype(np.float32)

            # 3. Whisper 모델에 전달
            recognized_text = self._get_model().transcribe(final_audio)

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
        if self.model is not None: return self.model
        try:
            self.model = WhisperAdapter(self.model_name, self.model_dir)
        except Exception as error:
            self._load_error_message = str(error)
            raise RuntimeError(self._load_error_message) from error
        return self.model

    def _normalize_text(self, text: str) -> str:
        return "".join(str(text).lower().split())

class WhisperAdapter:
    def __init__(self, model_name: str, model_dir: str = config.WHISPER_MODEL_DIR) -> None:
        import whisper
        model_path = Path(model_dir)
        model_path.mkdir(parents=True, exist_ok=True)
        self._model = whisper.load_model(model_name, download_root=str(model_path))

    def transcribe(self, samples) -> str:
        # 한글 강제 옵션 고정
        result = self._model.transcribe(samples, fp16=False, language="ko")
        return str(result.get("text", "")).strip()