from dataclasses import dataclass
from math import dist

import config
from core.game_state import GameState, MouthLandmarks


SOUND_LIMIT_REASON = "그들이 당신의 존재를 눈치채고 말았군요. 이를 어쩐다..."    # 큰 소리
MOUTH_MOVEMENT_REASON = "이런, 잡아먹혔네요. 반가워요, 새로운 플레이어님!"      # 입 움직임
FACE_MISSING_REASON = "결계가 붕괴되었습니다. 너무 고통스럽진 않길 빌어요."      # 카메라에 얼굴 안 보임

# frozen=True : 한 번 만들어진 뒤 값 바뀌지 않음
@dataclass(frozen=True)
class RuleEvaluation:
    """글로벌 규칙 평가 결과."""

    violated: bool
    reason: str | None = None


class GlobalRules:
    """모든 스테이지에서 공통으로 적용할 실패 규칙을 관리한다."""

    def __init__(
        self,
        mouth_tolerance_ratio: float = config.MOUTH_LANDMARK_TOLERANCE_RATIO,    # 입 움직였다고 판단할 기준
        mouth_fail_seconds: float = config.MOUTH_LANDMARK_FAIL_SECONDS,          # 입 움직임이 몇 초 이상 지속되면 규칙 위반인지
        face_missing_fail_seconds: float = config.FACE_MISSING_FAIL_SECONDS,     # 얼굴 몇 초 이상 안 보이면 규칙 위반인지
        audio_limit_db: float = config.AUDIO_LIMIT_DB,                           # 소리 몇 db 이상이면 규칙 위반인지
    ) -> None:
        self.mouth_tolerance_ratio = mouth_tolerance_ratio
        self.mouth_fail_seconds = mouth_fail_seconds
        self.face_missing_fail_seconds = face_missing_fail_seconds
        self.audio_limit_db = audio_limit_db
        self._mouth_violation_seconds = 0.0
        self._face_missing_seconds = 0.0

    # 실제 규칙 검사 함수
    # 1. 소리 크기 검사 -> 2. 얼굴 보이는지 검사 -> 3. 입 움직임 검사
    def evaluate(
        self,
        dt: float,
        baseline_mouth_landmarks: MouthLandmarks | None,
        current_mouth_landmarks: MouthLandmarks,
        face_detected: bool,
        audio_db: float,
        audio_is_fallback: bool = False,
    ) -> RuleEvaluation:
        
        # 1. 소리 크기 검사
        if not audio_is_fallback and audio_db >= self.audio_limit_db:
            return RuleEvaluation(violated=True, reason=SOUND_LIMIT_REASON)

        # 2. 얼굴 보이는지 검사
        face_result = self._evaluate_face_missing(dt, face_detected)
        if face_result.violated:
            return face_result

        # 3. 입 움직임 검사
        mouth_result = self._evaluate_mouth_movement(
            dt,
            baseline_mouth_landmarks,
            current_mouth_landmarks,
        )
        if mouth_result.violated:
            return mouth_result

        return RuleEvaluation(violated=False)

    # evaluate() 실행 후 규칙 위반이 있으면 상태를 "game_over"로 변환
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

    # 누적 시간 초기화 (게임 재시작시 호출)
    def reset(self) -> None:
        self._mouth_violation_seconds = 0.0
        self._face_missing_seconds = 0.0

    # 카메라에 얼굴 보이는지 검사
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

    # 입 움직임 검사
    def _evaluate_mouth_movement(
        self,
        dt: float,
        baseline_mouth_landmarks: MouthLandmarks | None,
        current_mouth_landmarks: MouthLandmarks,
    ) -> RuleEvaluation:
        
        # 입 좌표 비교 가능한지 확인
        if not self._has_comparable_mouth_landmarks(
            baseline_mouth_landmarks,
            current_mouth_landmarks,
        ):
            self._mouth_violation_seconds = 0.0
            return RuleEvaluation(violated=False)

        # 입 움직임이 있었으면 움직인 시간 누적
        if self._is_mouth_moved(baseline_mouth_landmarks, current_mouth_landmarks):
            self._mouth_violation_seconds += dt
        else: # 없었으면 0초로 초기화
            self._mouth_violation_seconds = 0.0

        return RuleEvaluation(
            violated=self._mouth_violation_seconds >= self.mouth_fail_seconds,
            reason=MOUTH_MOVEMENT_REASON
            if self._mouth_violation_seconds >= self.mouth_fail_seconds
            else None,
        )

    # 기준 입 좌표와 현재 입 좌표가 비교 가능한지 확인
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

    # 각 입 좌표 이동거리 계산
    # dist(baseline, current) : 두 점 사이 거리
    # 하나라도 허용 범위를 넘으면 움직였다고 판단
    def _is_mouth_moved(
        self,
        baseline_mouth_landmarks: MouthLandmarks,
        current_mouth_landmarks: MouthLandmarks,
    ) -> bool:
        return any(
            dist(baseline, current) > self.mouth_tolerance_ratio
            for baseline, current in zip(baseline_mouth_landmarks, current_mouth_landmarks)
        )
