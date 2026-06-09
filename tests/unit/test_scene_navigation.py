from types import SimpleNamespace

import pygame

from scenes.ending import EndingScene
from scenes.intro import IntroScene
from scenes.rules_guide import RulesGuideScene
from scenes.stage1 import Stage1Scene
from scenes.stage2 import Stage2Scene
from scenes.stage3 import Stage3Scene
from scenes.start_page import StartPageScene


def keydown_event(key: int) -> SimpleNamespace:
    return SimpleNamespace(type=pygame.KEYDOWN, key=key)


def test_space_key_moves_through_temporary_scene_flow():
    scenes_with_next_scene = [
        (StartPageScene(), "intro"),
        (IntroScene(), "rules_guide"),
        (RulesGuideScene(), "stage1"),
        (Stage3Scene(), "ending"),
    ]

    for scene, next_scene in scenes_with_next_scene:
        assert scene.handle_event(keydown_event(pygame.K_SPACE), object()) == next_scene


def test_stage1_scene_transitions_after_five_seconds():
    stage1 = Stage1Scene()

    assert stage1.update(dt=4.9, game_state=object(), services={}) is None
    assert stage1.update(dt=0.1, game_state=object(), services={}) == "stage2"


def test_escape_key_requests_quit_from_temporary_scenes():
    scenes = [
        StartPageScene(),
        IntroScene(),
        RulesGuideScene(),
        Stage1Scene(),
        Stage2Scene(),
        Stage3Scene(),
        EndingScene(),
    ]

    for scene in scenes:
        assert scene.handle_event(keydown_event(pygame.K_ESCAPE), object()) == "quit"


def test_ending_space_key_requests_quit():
    assert EndingScene().handle_event(keydown_event(pygame.K_SPACE), object()) == "quit"
