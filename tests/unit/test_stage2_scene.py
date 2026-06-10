from types import SimpleNamespace

import pygame

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


class FakeRules:
    def __init__(self) -> None:
        self.calls = []

    def apply_to_game_state(
        self,
        dt: float,
        game_state: GameState,
        face_detected: bool,
        audio_is_fallback: bool = False,
    ) -> str | None:
        self.calls.append((dt, game_state, face_detected, audio_is_fallback))
        return None


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


def keydown_event(key: int) -> SimpleNamespace:
    return SimpleNamespace(type=pygame.KEYDOWN, key=key)


def test_stage2_zero_key_moves_to_stage3():
    scene = Stage2Scene()

    assert scene.handle_event(keydown_event(pygame.K_0), GameState()) == "stage3"


def test_stage2_draw_after_intro_does_not_require_phase_state():
    scene = Stage2Scene()
    scene.intro_done = True

    pygame.font.init()
    screen = pygame.Surface((1280, 720))

    scene.draw(screen, GameState(), {})


def test_stage2_moves_to_stage3_when_time_expires_without_recognized_speech():
    speech = FakeSpeech(
        [
            silent_result("얄리얄리얄라성"),
        ]
    )
    scene = Stage2Scene()
    game_state = GameState(current_scene="stage2")
    services = {"speech": speech}

    assert scene.update(scene.intro_duration, game_state, services) is None
    assert speech.calls == []
    assert scene.update(0.1, game_state, services) is None
    assert scene.update(scene.time_limit, game_state, services) == "stage3"

    assert speech.calls == [
            ("얄리얄리얄라성", 5.0),
    ]
    assert scene.user_spoken_text == "(판독 불가)"
    assert scene.match_ratio_percent == 0.0
    assert game_state.stage_results[2] == "clear"


def test_stage2_enters_game_over_when_any_speech_is_recognized():
    speech = FakeSpeech(
        [
            spoken_result("나 여기 있어"),
        ]
    )
    scene = Stage2Scene()
    game_state = GameState(current_scene="stage2")
    services = {"speech": speech}

    assert scene.update(scene.intro_duration, game_state, services) is None
    transition = scene.update(0.1, game_state, services)

    assert transition is None
    assert game_state.is_game_over is False
    assert scene.user_spoken_text == "나 여기 있어"
    assert scene.match_ratio_percent == 100.0
    assert scene.audio_status == "FAILED_MATCH"

    transition = scene.update(2.9, game_state, services)

    assert transition is None
    assert game_state.is_game_over is False

    transition = scene.update(0.1, game_state, services)

    assert transition == "game_over"
    assert game_state.is_game_over is True
    assert game_state.game_over_reason == SOUND_LIMIT_REASON


def test_stage2_reset_returns_to_intro_state_after_pending_game_over():
    speech = FakeSpeech(
        [
            spoken_result("나 여기 있어"),
        ]
    )
    scene = Stage2Scene()
    game_state = GameState(current_scene="stage2")
    services = {"speech": speech}

    assert scene.update(scene.intro_duration, game_state, services) is None
    assert scene.update(0.1, game_state, services) is None

    scene.reset()

    assert scene.intro_done is False
    assert scene.audio_status == "RECORDING"
    assert scene.user_spoken_text == ""
    assert scene.match_ratio_percent == 0.0


def test_stage2_does_not_apply_global_rules_while_prompts_are_active():
    speech = FakeSpeech(
        [
            silent_result("나 여기 있어"),
        ]
    )
    rules = FakeRules()
    scene = Stage2Scene()
    game_state = GameState(current_scene="stage2")
    services = {"speech": speech, "rules": rules}

    assert scene.update(scene.intro_duration, game_state, services) is None
    assert scene.update(0.1, game_state, services) is None
    assert scene.update(scene.time_limit, game_state, services) == "stage3"

    assert len(rules.calls) == 1
