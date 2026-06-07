from unittest.mock import patch
from pathlib import Path

from core.speech import SpeechRecognitionResult, SpeechRecognizer, WhisperAdapter


class FakeRecorder:
    def __init__(self, samples):
        self.samples = samples
        self.calls = []

    def record(self, duration_seconds, sample_rate):
        self.calls.append((duration_seconds, sample_rate))
        return self.samples


class FakeWhisperModel:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def transcribe(self, samples):
        self.calls.append(samples)
        return self.text


class FailingWhisperModel:
    def transcribe(self, samples):
        raise RuntimeError("Whisper 오류")


class FakeWhisperPackage:
    def __init__(self):
        self.calls = []

    def load_model(self, model_name, download_root):
        self.calls.append((model_name, download_root))
        return object()


class FakeWhisperAdapter(WhisperAdapter):
    def __init__(self, whisper_package, model_name, model_dir):
        self.whisper_package = whisper_package
        super().__init__(model_name, model_dir)

    def _import_whisper(self):
        return self.whisper_package


def test_similarity_returns_one_for_same_target_text():
    recognizer = SpeechRecognizer(target_text="붉은 문을 열어라")

    similarity = recognizer.calculate_similarity("붉은 문을 열어라")

    assert similarity == 1.0


def test_recognize_returns_passed_result_when_similarity_is_high_enough():
    recorder = FakeRecorder(samples=[0.1, 0.2, 0.3])
    model = FakeWhisperModel(text="붉은 문을 열어라")
    recognizer = SpeechRecognizer(
        target_text="붉은 문을 열어라",
        recorder=recorder,
        model=model,
        pass_score=0.75,
    )

    result = recognizer.recognize(duration_seconds=2.5)

    assert result == SpeechRecognitionResult(
        target_text="붉은 문을 열어라",
        recognized_text="붉은 문을 열어라",
        similarity=1.0,
        passed=True,
    )
    assert recorder.calls == [(2.5, 16000)]
    assert model.calls == [[0.1, 0.2, 0.3]]


def test_recognize_returns_failed_result_when_similarity_is_too_low():
    recognizer = SpeechRecognizer(
        target_text="붉은 문을 열어라",
        recorder=FakeRecorder(samples=[]),
        model=FakeWhisperModel(text="아무 말"),
        pass_score=0.75,
    )

    result = recognizer.recognize(duration_seconds=1.0)

    assert result.passed is False
    assert result.similarity < 0.75


def test_recognize_returns_fallback_result_when_whisper_fails():
    recognizer = SpeechRecognizer(
        target_text="붉은 문을 열어라",
        recorder=FakeRecorder(samples=[]),
        model=FailingWhisperModel(),
    )

    result = recognizer.recognize(duration_seconds=1.0)

    assert result == SpeechRecognitionResult(
        target_text="붉은 문을 열어라",
        recognized_text="",
        similarity=0.0,
        passed=False,
        is_fallback=True,
        error_message="Whisper 오류",
    )


def test_whisper_adapter_loads_model_from_configured_model_directory():
    whisper_package = FakeWhisperPackage()
    model_dir = "assets/models"

    with patch("core.speech.Path.mkdir") as mkdir:
        FakeWhisperAdapter(whisper_package, "tiny", model_dir)

    assert whisper_package.calls == [("tiny", str(Path(model_dir)))]
    mkdir.assert_called_once_with(parents=True, exist_ok=True)
