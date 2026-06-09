from core.game_state import GameState
from core.rules import SOUND_LIMIT_REASON
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


def silent_result(target_text: str) -> SpeechRecognitionResult:
    return SpeechRecognitionResult(
        target_text=target_text,
        recognized_text="",
        similarity=0.0,
        passed=False,
    )


def spoken_result(target_text: str) -> SpeechRecognitionResult:
    return SpeechRecognitionResult(
        target_text=target_text,
        recognized_text="나 여기 있어",
        similarity=1.0,
        passed=True,
    )


def test_stage2_moves_to_stage3_only_when_no_speech_is_recognized():
    speech = FakeSpeech(
        [
            silent_result("나 여기 있어"),
            silent_result("내가 보이지 않니"),
            silent_result("살고 싶다면 지금 당장 소리 내어 읽으세요"),
        ]
    )
    scene = Stage2Scene()
    game_state = GameState(current_scene="stage2")
    services = {"speech": speech}

    assert scene.update(scene.intro_duration, game_state, services) is None
    assert speech.calls == []
    assert scene.update(0.1, game_state, services) is None
    assert scene.update(0.1, game_state, services) is None
    assert scene.update(0.1, game_state, services) == "stage3"

    assert speech.calls == [
        ("나 여기 있어", 10.0),
        ("내가 보이지 않니", 10.0),
        ("살고 싶다면 지금 당장 소리 내어 읽으세요", 10.0),
    ]
    assert game_state.stage_results[2] == "clear"


def test_stage2_enters_game_over_when_any_speech_is_recognized():
    speech = FakeSpeech([spoken_result("나 여기 있어")])
    scene = Stage2Scene()
    game_state = GameState(current_scene="stage2")

    first_transition = scene.update(scene.intro_duration, game_state, {"speech": speech})
    transition = scene.update(0.1, game_state, {"speech": speech})

    assert first_transition is None
    assert transition == "game_over"
    assert game_state.is_game_over is True
    assert game_state.game_over_reason == SOUND_LIMIT_REASON
    assert scene.user_spoken_text == "나 여기 있어"
    assert scene.match_ratio_percent == 100.0
