from main import (
    SERVICE_NAMES,
    apply_scene_transition,
    create_scenes,
    create_services,
    release_services,
)
from core.audio import AudioMeter
from core.camera import Camera
from core.detector import Detector
from core.face_tracker import FaceTracker
from core.game_state import GameState
from core.speech import SpeechRecognizer
from scenes.ending import EndingScene
from scenes.game_over import GameOverScene
from scenes.intro import IntroScene
from scenes.stage1 import Stage1Scene
from scenes.stage2 import Stage2Scene
from scenes.stage3 import Stage3Scene
from scenes.start_page import StartPageScene


def test_create_services_prepares_common_service_keys():
    services = create_services()

    assert tuple(services.keys()) == SERVICE_NAMES
    assert isinstance(services["camera"], Camera)
    assert isinstance(services["audio"], AudioMeter)
    assert isinstance(services["face_tracker"], FaceTracker)
    assert isinstance(services["detector"], Detector)
    assert isinstance(services["speech"], SpeechRecognizer)
    assert services["rules"] is None


def test_release_services_releases_releasable_services():
    class FakeService:
        def __init__(self):
            self.released = False

        def release(self):
            self.released = True

    camera = FakeService()
    audio = FakeService()

    release_services({"camera": camera, "audio": audio})

    assert camera.released is True
    assert audio.released is True


def test_create_scenes_registers_all_scene_names():
    scenes = create_scenes()

    assert scenes.keys() == {
        "start",
        "intro",
        "stage1",
        "stage2",
        "stage3",
        "ending",
        "game_over",
    }
    assert isinstance(scenes["start"], StartPageScene)
    assert isinstance(scenes["intro"], IntroScene)
    assert isinstance(scenes["stage1"], Stage1Scene)
    assert isinstance(scenes["stage2"], Stage2Scene)
    assert isinstance(scenes["stage3"], Stage3Scene)
    assert isinstance(scenes["ending"], EndingScene)
    assert isinstance(scenes["game_over"], GameOverScene)


def test_apply_scene_transition_updates_current_scene():
    game_state = GameState()

    should_keep_running = apply_scene_transition("intro", game_state)

    assert should_keep_running is True
    assert game_state.current_scene == "intro"


def test_apply_scene_transition_keeps_scene_when_transition_is_none():
    game_state = GameState(current_scene="stage1")

    should_keep_running = apply_scene_transition(None, game_state)

    assert should_keep_running is True
    assert game_state.current_scene == "stage1"


def test_apply_scene_transition_stops_loop_for_quit():
    game_state = GameState(current_scene="ending")

    should_keep_running = apply_scene_transition("quit", game_state)

    assert should_keep_running is False
    assert game_state.current_scene == "ending"
