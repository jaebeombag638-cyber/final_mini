import inspect

from core.scene import Scene
from scenes.ending import EndingScene
from scenes.game_over import GameOverScene
from scenes.intro import IntroScene
from scenes.stage1 import Stage1Scene
from scenes.stage2 import Stage2Scene
from scenes.stage3 import Stage3Scene
from scenes.start_page import StartPageScene


SCENE_CLASSES = [
    StartPageScene,
    IntroScene,
    Stage1Scene,
    Stage2Scene,
    Stage3Scene,
    EndingScene,
    GameOverScene,
]


def test_scene_base_defines_common_methods():
    assert inspect.signature(Scene.handle_event) == inspect.Signature(
        parameters=[
            inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("event", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("game_state", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        ],
        return_annotation=str | None,
    )
    assert inspect.signature(Scene.update) == inspect.Signature(
        parameters=[
            inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("dt", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("game_state", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("services", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        ],
        return_annotation=str | None,
    )
    assert inspect.signature(Scene.draw) == inspect.Signature(
        parameters=[
            inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("screen", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("game_state", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("services", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        ],
        return_annotation=None,
    )


def test_all_scene_classes_follow_common_interface():
    for scene_class in SCENE_CLASSES:
        assert issubclass(scene_class, Scene)
        scene = scene_class()

        assert scene.handle_event(event=object(), game_state=object()) is None
        assert scene.update(dt=0.016, game_state=object(), services={}) is None
        assert scene.draw(screen=object(), game_state=object(), services={}) is None
