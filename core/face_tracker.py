from collections.abc import Callable
from dataclasses import dataclass
from math import dist
from pathlib import Path
from typing import Any

import config


LEFT_MOUTH_CORNER = 61
RIGHT_MOUTH_CORNER = 291
UPPER_LIP = 13
LOWER_LIP = 14
MOUTH_LANDMARK_INDICES = (
    LEFT_MOUTH_CORNER,
    RIGHT_MOUTH_CORNER,
    UPPER_LIP,
    LOWER_LIP,
)
MouthLandmark = tuple[float, float]
MouthLandmarks = tuple[MouthLandmark, ...]


@dataclass(frozen=True)
class FaceTrackingResult:
    """얼굴 추적 결과와 fallback 상태를 함께 담는다."""

    face_detected: bool
    mouth_landmarks: MouthLandmarks
    is_fallback: bool = False
    error_message: str | None = None


class FaceTracker:
    """MediaPipe 얼굴 랜드마크 결과를 게임 규칙용 입 좌표로 변환한다."""

    def __init__(
        self,
        landmarker: Any | None = None,
        landmarker_factory: Callable[[], Any] | None = None,
        check_interval_seconds: float = config.FACE_TRACK_INTERVAL_SECONDS,
    ) -> None:
        self.landmarker = landmarker
        self.landmarker_factory = landmarker_factory
        self.check_interval_seconds = check_interval_seconds
        self.baseline_mouth_landmarks: MouthLandmarks | None = None
        self.last_raw_mouth_landmarks: MouthLandmarks = ()
        self._last_checked_at: float | None = None
        self._last_result: FaceTrackingResult | None = None
        self._load_error_message: str | None = None

    def track(self, frame, now: float) -> FaceTrackingResult:
        if self._should_use_cache(now):
            return self._last_result

        landmarker = self._get_landmarker()
        if landmarker is None:
            return self._cache_result(
                FaceTrackingResult(
                    face_detected=False,
                    mouth_landmarks=(),
                    is_fallback=True,
                    error_message=self._load_error_message,
                ),
                now,
            )

        try:
            face_landmarks = landmarker.detect(frame)
            mouth_landmarks = self.extract_mouth_landmarks(face_landmarks)
        except Exception as error:
            return self._cache_result(
                FaceTrackingResult(
                    face_detected=False,
                    mouth_landmarks=(),
                    is_fallback=True,
                    error_message=str(error),
                ),
                now,
            )

        if mouth_landmarks == ():
            return self._cache_result(
                FaceTrackingResult(face_detected=False, mouth_landmarks=()),
                now,
            )

        return self._cache_result(
            FaceTrackingResult(face_detected=True, mouth_landmarks=mouth_landmarks),
            now,
        )

    def calibrate(self, frame, now: float) -> FaceTrackingResult:
        result = self.track(frame, now)
        if result.face_detected:
            self.baseline_mouth_landmarks = result.mouth_landmarks
        return result

    def calculate_mouth_differences(
        self,
        baseline: MouthLandmarks,
        current: MouthLandmarks,
    ) -> tuple[float, ...]:
        return tuple(
            round(dist(baseline_landmark, current_landmark), 4)
            for baseline_landmark, current_landmark in zip(baseline, current)
        )

    def extract_mouth_landmarks(self, face_landmarks) -> MouthLandmarks:
        landmarks = self._select_first_face(face_landmarks)
        if not landmarks:
            self.last_raw_mouth_landmarks = ()
            return ()

        try:
            left_corner = self._point(landmarks[LEFT_MOUTH_CORNER])
            right_corner = self._point(landmarks[RIGHT_MOUTH_CORNER])
            upper_lip = self._point(landmarks[UPPER_LIP])
            lower_lip = self._point(landmarks[LOWER_LIP])
        except (IndexError, TypeError, AttributeError):
            self.last_raw_mouth_landmarks = ()
            return ()

        mouth_width = dist(left_corner, right_corner)
        if mouth_width == 0:
            self.last_raw_mouth_landmarks = ()
            return ()

        self.last_raw_mouth_landmarks = (
            left_corner,
            right_corner,
            upper_lip,
            lower_lip,
        )
        center = (
            (left_corner[0] + right_corner[0]) / 2,
            (left_corner[1] + right_corner[1]) / 2,
        )
        return tuple(
            self._normalize(point, center, mouth_width)
            for point in (left_corner, right_corner, upper_lip, lower_lip)
        )

    def release(self) -> None:
        if self.landmarker is not None and hasattr(self.landmarker, "close"):
            self.landmarker.close()
        self.landmarker = None

    def _should_use_cache(self, now: float) -> bool:
        return (
            self._last_result is not None
            and self._last_checked_at is not None
            and now - self._last_checked_at < self.check_interval_seconds
        )

    def _cache_result(
        self,
        result: FaceTrackingResult,
        now: float,
    ) -> FaceTrackingResult:
        self._last_result = result
        self._last_checked_at = now
        return result

    def _get_landmarker(self):
        if self.landmarker is not None:
            return self.landmarker

        try:
            factory = self.landmarker_factory or self._create_default_landmarker
            self.landmarker = factory()
        except Exception as error:
            self._load_error_message = str(error)
            self.landmarker = None

        return self.landmarker

    def _create_default_landmarker(self):
        return MediapipeFaceLandmarkerAdapter(config.FACE_LANDMARKER_MODEL_PATH)

    def _select_first_face(self, face_landmarks):
        if hasattr(face_landmarks, "face_landmarks"):
            face_landmarks = face_landmarks.face_landmarks
        if not face_landmarks:
            return ()
        first_item = face_landmarks[0]
        if hasattr(first_item, "x") and hasattr(first_item, "y"):
            return face_landmarks
        return face_landmarks[0]

    def _point(self, landmark) -> MouthLandmark:
        if hasattr(landmark, "x") and hasattr(landmark, "y"):
            return (float(landmark.x), float(landmark.y))
        return (float(landmark[0]), float(landmark[1]))

    def _normalize(
        self,
        point: MouthLandmark,
        center: MouthLandmark,
        mouth_width: float,
    ) -> MouthLandmark:
        return (
            round((point[0] - center[0]) / mouth_width, 4),
            round((point[1] - center[1]) / mouth_width, 4),
        )


class MediapipeFaceLandmarkerAdapter:
    """MediaPipe Face Landmarker 호출부를 FaceTracker에서 분리한다."""

    def __init__(self, model_path: str) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Face Landmarker 모델 파일이 없습니다: {model_path}")

        mp = self._import_mediapipe()
        base_options = mp.tasks.BaseOptions(model_asset_path=str(self.model_path))
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_faces=1,
        )
        self._mp = mp
        self._landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(options)

    def detect(self, bgr_frame):
        mp_image = self._create_image(bgr_frame)
        return self._landmarker.detect(mp_image)

    def close(self) -> None:
        self._landmarker.close()

    def _create_image(self, bgr_frame):
        rgb_frame = bgr_frame[:, :, ::-1]
        return self._mp.Image(
            image_format=self._mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

    def _import_mediapipe(self):
        import mediapipe as mp

        return mp
