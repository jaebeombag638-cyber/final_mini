from types import SimpleNamespace

from core.audio import AudioLevel
from core.face_tracker import FaceTrackingResult
from core.game_state import GameState
from scenes.stage1 import Stage1Scene
from scenes.stage2 import Stage2Scene
from scenes.stage3 import Stage3Scene


BASELINE_MOUTH = (
    (-0.5, 0.0),
    (0.5, 0.0),
    (0.0, -0.25),
    (0.0, 0.25),
)
CURRENT_MOUTH = (
    (-0.5, 0.2),
    (0.5, 0.0),
    (0.0, -0.25),
    (0.0, 0.25),
)


class FakeCamera:
    def __init__(self) -> None:
        self.open_called = False
        self.read_called = False

    def open(self) -> bool:
        self.open_called = True
        return True

    def read_frame(self):
        self.read_called = True
        return SimpleNamespace(image="frame")


class FakeAudio:
    def __init__(self) -> None:
        self.start_called = False

    def start(self) -> bool:
        self.start_called = True
        return True

    def read_db(self) -> AudioLevel:
        return AudioLevel(db=40.0)


class FakeFaceTracker:
    baseline_mouth_landmarks = BASELINE_MOUTH

    def __init__(self) -> None:
        self.track_calls = []

    def track(self, frame, now: float) -> FaceTrackingResult:
        self.track_calls.append((frame, now))
        return FaceTrackingResult(
            face_detected=True,
            mouth_landmarks=CURRENT_MOUTH,
        )


class FakeRules:
    def __init__(self, transition: str | None = None) -> None:
        self.transition = transition
        self.calls = []

    def apply_to_game_state(
        self,
        dt: float,
        game_state: GameState,
        face_detected: bool,
        audio_is_fallback: bool = False,
    ) -> str | None:
        self.calls.append((dt, game_state, face_detected, audio_is_fallback))
        return self.transition


def make_services(rules: FakeRules):
    return {
        "camera": FakeCamera(),
        "audio": FakeAudio(),
        "face_tracker": FakeFaceTracker(),
        "rules": rules,
    }


def test_stage_scenes_apply_global_rules_before_normal_transition():
    for scene_class in (Stage1Scene, Stage2Scene, Stage3Scene):
        rules = FakeRules(transition="game_over")
        services = make_services(rules)
        game_state = GameState(current_scene="stage1")
        scene = scene_class()

        transition = scene.update(0.1, game_state, services)

        assert transition == "game_over"
        assert services["camera"].open_called is True
        assert services["camera"].read_called is True
        assert services["audio"].start_called is True
        assert services["face_tracker"].track_calls == [("frame", 0.1)]
        assert game_state.current_audio_db == 40.0
        assert game_state.baseline_mouth_landmarks == BASELINE_MOUTH
        assert game_state.current_mouth_landmarks == CURRENT_MOUTH
        assert rules.calls == [(0.1, game_state, True, False)]


def test_stage_timer_transition_runs_when_global_rules_pass():
    rules = FakeRules()
    services = make_services(rules)
    scene = Stage1Scene()

    transition = scene.update(5.0, GameState(), services)

    assert transition == "stage2"
    assert len(rules.calls) == 1
