import inspect

from core.scene import Scene


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
