from core.game_state import GameState


def test_game_state_defaults_hold_shared_scene_data():
    game_state = GameState()

    assert game_state.current_scene == "start"
    assert game_state.baseline_mouth_landmarks is None
    assert game_state.current_mouth_landmarks == ()
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


def test_game_state_tracks_stage_results():
    game_state = GameState()

    assert game_state.stage_results == {
        1: "pending",
        2: "pending",
        3: "pending",
    }

    game_state.mark_stage_clear(1)
    assert game_state.current_stage == 1
    assert game_state.stage_results[1] == "clear"

    game_state.mark_stage_failed(2)
    assert game_state.current_stage == 2
    assert game_state.stage_results[2] == "failed"


def test_game_state_updates_shared_scene_data():
    game_state = GameState()
    baseline_landmarks = (
        (0.0, 0.5),
        (1.0, 0.5),
        (0.5, 0.3),
        (0.5, 0.7),
    )
    current_landmarks = (
        (0.0, 0.52),
        (1.0, 0.51),
        (0.5, 0.31),
        (0.5, 0.69),
    )

    game_state.change_scene("stage1")
    game_state.update_mouth_landmarks(
        baseline=baseline_landmarks,
        current=current_landmarks,
    )
    game_state.update_audio_db(42.5)

    assert game_state.current_scene == "stage1"
    assert game_state.baseline_mouth_landmarks == baseline_landmarks
    assert game_state.current_mouth_landmarks == current_landmarks
    assert game_state.current_audio_db == 42.5
