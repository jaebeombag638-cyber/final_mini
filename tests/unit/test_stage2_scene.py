from core.game_state import GameState
from core.speech import SpeechRecognitionResult
from scenes.stage2 import Stage2Scene


class FakeSpeech:
    def __init__(self, results) -> None:
        self.results = list(results)
        self.calls = []
        self.target_text = ""

    def recognize(self, duration_seconds: float):
        self.calls.append((self.target_text, duration_seconds))
        return self.results.pop(0)


def passed_result(target_text: str) -> SpeechRecognitionResult:
    return SpeechRecognitionResult(
        target_text=target_text,
        recognized_text=target_text,
        similarity=1.0,
        passed=True,
    )


def failed_result(target_text: str) -> SpeechRecognitionResult:
    return SpeechRecognitionResult(
        target_text=target_text,
        recognized_text="다른 말",
        similarity=0.0,
        passed=False,
    )


def test_stage2_records_each_phase_for_ten_seconds_before_stage3():
    speech = FakeSpeech(
        [
            passed_result("나 여기 있어"),
            passed_result("내가 보이지 않니"),
            passed_result("살고 싶다면 지금 당장 소리 내어 읽으세요"),
        ]
    )
    scene = Stage2Scene()
    game_state = GameState(current_scene="stage2")
    services = {"speech": speech}

    assert scene.update(2.0, game_state, services) is None
    assert scene.update(0.1, game_state, services) is None
    assert scene.update(0.1, game_state, services) == "stage3"

    assert speech.calls == [
        ("나 여기 있어", 10.0),
        ("내가 보이지 않니", 10.0),
        ("살고 싶다면 지금 당장 소리 내어 읽으세요", 10.0),
    ]
    assert game_state.stage_results[2] == "clear"


def test_stage2_enters_game_over_when_speech_does_not_match():
    speech = FakeSpeech([failed_result("나 여기 있어")])
    scene = Stage2Scene()
    game_state = GameState(current_scene="stage2")

    transition = scene.update(2.0, game_state, {"speech": speech})

    assert transition == "game_over"
    assert game_state.is_game_over is True
    assert game_state.game_over_reason == "음성 인식 실패"
