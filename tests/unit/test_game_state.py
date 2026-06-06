from core.game_state import GameState


def test_game_state_defaults_hold_shared_scene_data():
    game_state = GameState()

    assert game_state.current_scene == "start"
    assert game_state.baseline_emotion is None
    assert game_state.current_emotion == "unknown"
    assert game_state.current_audio_db == 0.0
    assert game_state.current_stage == 0
    assert game_state.is_game_over is False
    assert game_state.reached_ending is False
    assert game_state.game_over_reason is None


def test_game_state_can_enter_game_over_and_ending():
    game_state = GameState()

    game_state.enter_game_over("sound_limit")
    assert game_state.is_game_over is True
    assert game_state.current_scene == "game_over"
    assert game_state.game_over_reason == "sound_limit"

    game_state.reach_ending()
    assert game_state.reached_ending is True
    assert game_state.current_scene == "ending"
