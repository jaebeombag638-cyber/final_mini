from dataclasses import dataclass
from math import dist

import config
from core.game_state import GameState, MouthLandmarks


SOUND_LIMIT_REASON = "sound_limit"
MOUTH_MOVEMENT_REASON = "mouth_movement"
FACE_MISSING_REASON = "face_missing"


@dataclass(frozen=True)
class RuleEvaluation:
    """글로벌 규칙 평가 결과."""

    violated: bool
    reason: str | None = None


class GlobalRules:
    """모든 스테이지에서 공통으로 적용할 실패 규칙을 관리한다."""

    def __init__(
        self,
        mouth_tolerance_ratio: float = config.MOUTH_LANDMARK_TOLERANCE_RATIO,
        mouth_fail_seconds: float = config.MOUTH_LANDMARK_FAIL_SECONDS,
        face_missing_fail_seconds: float = config.FACE_MISSING_FAIL_SECONDS,
        audio_limit_db: float = config.AUDIO_LIMIT_DB,
    ) -> None:
        self.mouth_tolerance_ratio = mouth_tolerance_ratio
        self.mouth_fail_seconds = mouth_fail_seconds
        self.face_missing_fail_seconds = face_missing_fail_seconds
        self.audio_limit_db = audio_limit_db
        self._mouth_violation_seconds = 0.0
        self._face_missing_seconds = 0.0

    def evaluate(
        self,
        dt: float,
        baseline_mouth_landmarks: MouthLandmarks | None,
        current_mouth_landmarks: MouthLandmarks,
        face_detected: bool,
        audio_db: float,
        audio_is_fallback: bool = False,
    ) -> RuleEvaluation:
        if not audio_is_fallback and audio_db >= self.audio_limit_db:
            return RuleEvaluation(violated=True, reason=SOUND_LIMIT_REASON)

        face_result = self._evaluate_face_missing(dt, face_detected)
        if face_result.violated:
            return face_result

        mouth_result = self._evaluate_mouth_movement(
            dt,
            baseline_mouth_landmarks,
            current_mouth_landmarks,
        )
        if mouth_result.violated:
            return mouth_result

        return RuleEvaluation(violated=False)

    def apply_to_game_state(
        self,
        dt: float,
        game_state: GameState,
        face_detected: bool,
        audio_is_fallback: bool = False,
    ) -> str | None:
        result = self.evaluate(
            dt=dt,
            baseline_mouth_landmarks=game_state.baseline_mouth_landmarks,
            current_mouth_landmarks=game_state.current_mouth_landmarks,
            face_detected=face_detected,
            audio_db=game_state.current_audio_db,
            audio_is_fallback=audio_is_fallback,
        )
        if not result.violated:
            return None

        game_state.enter_game_over(result.reason)
        return "game_over"

    def reset(self) -> None:
        self._mouth_violation_seconds = 0.0
        self._face_missing_seconds = 0.0

    def _evaluate_face_missing(self, dt: float, face_detected: bool) -> RuleEvaluation:
        if face_detected:
            self._face_missing_seconds = 0.0
            return RuleEvaluation(violated=False)

        self._face_missing_seconds += dt
        return RuleEvaluation(
            violated=self._face_missing_seconds >= self.face_missing_fail_seconds,
            reason=FACE_MISSING_REASON
            if self._face_missing_seconds >= self.face_missing_fail_seconds
            else None,
        )

    def _evaluate_mouth_movement(
        self,
        dt: float,
        baseline_mouth_landmarks: MouthLandmarks | None,
        current_mouth_landmarks: MouthLandmarks,
    ) -> RuleEvaluation:
        if not self._has_comparable_mouth_landmarks(
            baseline_mouth_landmarks,
            current_mouth_landmarks,
        ):
            self._mouth_violation_seconds = 0.0
            return RuleEvaluation(violated=False)

        if self._is_mouth_moved(baseline_mouth_landmarks, current_mouth_landmarks):
            self._mouth_violation_seconds += dt
        else:
            self._mouth_violation_seconds = 0.0

        return RuleEvaluation(
            violated=self._mouth_violation_seconds >= self.mouth_fail_seconds,
            reason=MOUTH_MOVEMENT_REASON
            if self._mouth_violation_seconds >= self.mouth_fail_seconds
            else None,
        )

    def _has_comparable_mouth_landmarks(
        self,
        baseline_mouth_landmarks: MouthLandmarks | None,
        current_mouth_landmarks: MouthLandmarks,
    ) -> bool:
        return (
            baseline_mouth_landmarks is not None
            and len(baseline_mouth_landmarks) == len(current_mouth_landmarks)
            and len(current_mouth_landmarks) > 0
        )

    def _is_mouth_moved(
        self,
        baseline_mouth_landmarks: MouthLandmarks,
        current_mouth_landmarks: MouthLandmarks,
    ) -> bool:
        return any(
            dist(baseline, current) > self.mouth_tolerance_ratio
            for baseline, current in zip(baseline_mouth_landmarks, current_mouth_landmarks)
        )
