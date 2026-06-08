from core.game_state import GameState
from core.rules import GlobalRules, RuleEvaluation


BASELINE_MOUTH = (
    (-0.5, 0.0),
    (0.5, 0.0),
    (0.0, -0.25),
    (0.0, 0.25),
)


def test_sound_limit_returns_game_over_reason_immediately():
    rules = GlobalRules(audio_limit_db=65.0)

    result = rules.evaluate(
        dt=0.1,
        baseline_mouth_landmarks=BASELINE_MOUTH,
        current_mouth_landmarks=BASELINE_MOUTH,
        face_detected=True,
        audio_db=65.0,
    )

    assert result == RuleEvaluation(violated=True, reason="sound_limit")


def test_microphone_fallback_does_not_trigger_sound_limit():
    rules = GlobalRules(audio_limit_db=65.0)

    result = rules.evaluate(
        dt=0.1,
        baseline_mouth_landmarks=BASELINE_MOUTH,
        current_mouth_landmarks=BASELINE_MOUTH,
        face_detected=True,
        audio_db=90.0,
        audio_is_fallback=True,
    )

    assert result == RuleEvaluation(violated=False, reason=None)


def test_mouth_change_must_continue_until_fail_seconds():
    moved_mouth = (
        (-0.5, 0.2),
        (0.5, 0.0),
        (0.0, -0.25),
        (0.0, 0.25),
    )
    rules = GlobalRules(mouth_tolerance_ratio=0.12, mouth_fail_seconds=2.0)

    first_result = rules.evaluate(
        dt=1.0,
        baseline_mouth_landmarks=BASELINE_MOUTH,
        current_mouth_landmarks=moved_mouth,
        face_detected=True,
        audio_db=0.0,
    )
    second_result = rules.evaluate(
        dt=1.0,
        baseline_mouth_landmarks=BASELINE_MOUTH,
        current_mouth_landmarks=moved_mouth,
        face_detected=True,
        audio_db=0.0,
    )

    assert first_result == RuleEvaluation(violated=False, reason=None)
    assert second_result == RuleEvaluation(violated=True, reason="mouth_movement")


def test_mouth_timer_resets_when_mouth_returns_to_baseline():
    moved_mouth = (
        (-0.5, 0.2),
        (0.5, 0.0),
        (0.0, -0.25),
        (0.0, 0.25),
    )
    rules = GlobalRules(mouth_tolerance_ratio=0.12, mouth_fail_seconds=2.0)

    rules.evaluate(
        dt=1.5,
        baseline_mouth_landmarks=BASELINE_MOUTH,
        current_mouth_landmarks=moved_mouth,
        face_detected=True,
        audio_db=0.0,
    )
    stable_result = rules.evaluate(
        dt=0.1,
        baseline_mouth_landmarks=BASELINE_MOUTH,
        current_mouth_landmarks=BASELINE_MOUTH,
        face_detected=True,
        audio_db=0.0,
    )
    moved_again_result = rules.evaluate(
        dt=0.6,
        baseline_mouth_landmarks=BASELINE_MOUTH,
        current_mouth_landmarks=moved_mouth,
        face_detected=True,
        audio_db=0.0,
    )

    assert stable_result == RuleEvaluation(violated=False, reason=None)
    assert moved_again_result == RuleEvaluation(violated=False, reason=None)


def test_face_missing_must_continue_until_fail_seconds():
    rules = GlobalRules(face_missing_fail_seconds=2.0)

    first_result = rules.evaluate(
        dt=1.0,
        baseline_mouth_landmarks=BASELINE_MOUTH,
        current_mouth_landmarks=(),
        face_detected=False,
        audio_db=0.0,
    )
    second_result = rules.evaluate(
        dt=1.0,
        baseline_mouth_landmarks=BASELINE_MOUTH,
        current_mouth_landmarks=(),
        face_detected=False,
        audio_db=0.0,
    )

    assert first_result == RuleEvaluation(violated=False, reason=None)
    assert second_result == RuleEvaluation(violated=True, reason="face_missing")


def test_apply_to_game_state_enters_game_over_when_rule_is_violated():
    game_state = GameState(
        baseline_mouth_landmarks=BASELINE_MOUTH,
        current_mouth_landmarks=BASELINE_MOUTH,
        current_audio_db=70.0,
    )
    rules = GlobalRules(audio_limit_db=65.0)

    result = rules.apply_to_game_state(
        dt=0.1,
        game_state=game_state,
        face_detected=True,
    )

    assert result == "game_over"
    assert game_state.is_game_over is True
    assert game_state.game_over_reason == "sound_limit"
