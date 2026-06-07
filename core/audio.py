from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import config


@dataclass(frozen=True)
class AudioLevel:
    """현재 소리 크기와 fallback 여부를 함께 담는다."""

    db: float
    is_fallback: bool = False


class AudioMeter:
    """마이크 입력을 게임 규칙에서 쓰기 쉬운 상대 데시벨로 변환한다."""

    def __init__(
        self,
        sample_rate: int = 16000,
        block_size: int = 1024,
        channels: int = 1,
        threshold_db: float = config.AUDIO_LIMIT_DB,
        stream_factory: Callable[..., Any] | None = None,
        reference_rms: float = 0.00001,
    ) -> None:
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels
        self.threshold_db = threshold_db
        self.stream_factory = stream_factory
        self.reference_rms = reference_rms
        self._stream = None
        self._latest_samples = None

    @property
    def is_opened(self) -> bool:
        return self._stream is not None

    def start(self) -> bool:
        if self._stream is not None:
            return True

        try:
            self._stream = self._create_stream()
            self._stream.start()
        except Exception:
            self._stream = None
            return False

        return True

    def read_db(self) -> AudioLevel:
        if self._stream is None or self._latest_samples is None:
            return AudioLevel(db=0.0, is_fallback=True)

        rms = self.calculate_rms(self._latest_samples)
        db = self.calculate_relative_db(rms)
        return AudioLevel(db=db)

    def is_over_threshold(self, db: float | None = None) -> bool:
        current_db = self.read_db().db if db is None else db
        return current_db >= self.threshold_db

    def release(self) -> None:
        if self._stream is not None:
            self._stream.close()
            self._stream = None

    def _create_stream(self):
        if self.stream_factory is not None:
            return self.stream_factory(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                channels=self.channels,
                callback=self._on_audio_block,
            )

        sounddevice = self._import_sounddevice()
        return sounddevice.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=self.channels,
            callback=self._on_audio_block,
        )

    def _on_audio_block(self, indata, frames, time, status) -> None:
        try:
            self._latest_samples = indata.copy()
        except AttributeError:
            self._latest_samples = indata

    def calculate_rms(self, samples) -> float:
        np = self._import_numpy()
        values = np.asarray(samples, dtype=np.float32)
        if values.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(values))))

    def calculate_relative_db(self, rms: float) -> float:
        if rms <= 0:
            return 0.0

        np = self._import_numpy()
        db = 20 * np.log10(rms / self.reference_rms)
        return round(max(float(db), 0.0), 1)

    def _import_numpy(self):
        import numpy as np

        return np

    def _import_sounddevice(self):
        import sounddevice

        return sounddevice
