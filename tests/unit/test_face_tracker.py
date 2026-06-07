from dataclasses import dataclass

from core.face_tracker import (
    FaceTracker,
    FaceTrackingResult,
    MOUTH_LANDMARK_INDICES,
)


@dataclass(frozen=True)
class FakeLandmark:
    x: float
    y: float


class FakeLandmarker:
    def __init__(self, detections):
        self.detections = list(detections)
        self.detect_calls = 0
        self.closed = False

    def detect(self, frame):
        self.detect_calls += 1
        if not self.detections:
            return []
        return self.detections.pop(0)

    def close(self):
        self.closed = True


class FailingLandmarker:
    def detect(self, frame):
        raise RuntimeError("MediaPipe 오류")


def make_face_landmarks(
    left=(0.4, 0.5),
    right=(0.6, 0.5),
    upper=(0.5, 0.45),
    lower=(0.5, 0.55),
):
    landmarks = [FakeLandmark(0.0, 0.0) for _ in range(max(MOUTH_LANDMARK_INDICES) + 1)]
    landmarks[61] = FakeLandmark(*left)
    landmarks[291] = FakeLandmark(*right)
    landmarks[13] = FakeLandmark(*upper)
    landmarks[14] = FakeLandmark(*lower)
    return landmarks


def test_track_extracts_normalized_mouth_landmarks():
    landmarker = FakeLandmarker([make_face_landmarks()])
    tracker = FaceTracker(landmarker=landmarker)

    result = tracker.track(frame=object(), now=1.0)

    assert result.face_detected is True
    assert tracker.last_raw_mouth_landmarks == (
        (0.6, 0.5),
        (0.4, 0.5),
        (0.5, 0.45),
        (0.5, 0.55),
    )
    assert result.mouth_landmarks == (
        (0.5, 0.0),
        (-0.5, 0.0),
        (0.0, -0.25),
        (0.0, 0.25),
    )


def test_track_can_keep_original_mediapipe_coordinates():
    landmarker = FakeLandmarker([make_face_landmarks()])
    tracker = FaceTracker(landmarker=landmarker, mirror_coordinates=False)

    result = tracker.track(frame=object(), now=1.0)

    assert result.face_detected is True
    assert tracker.last_raw_mouth_landmarks == (
        (0.4, 0.5),
        (0.6, 0.5),
        (0.5, 0.45),
        (0.5, 0.55),
    )
    assert result.mouth_landmarks == (
        (-0.5, 0.0),
        (0.5, 0.0),
        (0.0, -0.25),
        (0.0, 0.25),
    )


def test_normalized_landmarks_do_not_change_when_face_moves_on_screen():
    first_face = make_face_landmarks()
    moved_face = make_face_landmarks(
        left=(0.5, 0.6),
        right=(0.7, 0.6),
        upper=(0.6, 0.55),
        lower=(0.6, 0.65),
    )
    tracker = FaceTracker(landmarker=FakeLandmarker([first_face, moved_face]))

    first_result = tracker.track(frame=object(), now=1.0)
    moved_result = tracker.track(frame=object(), now=2.0)

    assert moved_result.mouth_landmarks == first_result.mouth_landmarks


def test_calibrate_stores_baseline_mouth_landmarks():
    tracker = FaceTracker(landmarker=FakeLandmarker([make_face_landmarks()]))

    result = tracker.calibrate(frame=object(), now=1.0)

    assert result.face_detected is True
    assert tracker.baseline_mouth_landmarks == result.mouth_landmarks


def test_calculate_mouth_differences_compares_baseline_and_current():
    tracker = FaceTracker(landmarker=FakeLandmarker([]))
    baseline = (
        (-0.5, 0.0),
        (0.5, 0.0),
        (0.0, -0.25),
        (0.0, 0.25),
    )
    current = (
        (-0.5, 0.1),
        (0.5, 0.0),
        (0.0, -0.4),
        (0.0, 0.45),
    )

    differences = tracker.calculate_mouth_differences(baseline, current)

    assert differences == (0.1, 0.0, 0.15, 0.2)


def test_track_returns_no_face_state_when_landmarker_finds_no_face():
    tracker = FaceTracker(landmarker=FakeLandmarker([[]]))

    result = tracker.track(frame=object(), now=1.0)

    assert result == FaceTrackingResult(face_detected=False, mouth_landmarks=())


def test_track_reuses_cached_result_inside_check_interval():
    landmarker = FakeLandmarker([make_face_landmarks(), []])
    tracker = FaceTracker(landmarker=landmarker, check_interval_seconds=0.5)

    first_result = tracker.track(frame=object(), now=1.0)
    cached_result = tracker.track(frame=object(), now=1.2)

    assert cached_result == first_result
    assert landmarker.detect_calls == 1


def test_track_returns_fallback_when_landmarker_raises_error():
    tracker = FaceTracker(landmarker=FailingLandmarker())

    result = tracker.track(frame=object(), now=1.0)

    assert result.face_detected is False
    assert result.is_fallback is True
    assert result.error_message == "MediaPipe 오류"


def test_release_closes_landmarker():
    landmarker = FakeLandmarker([])
    tracker = FaceTracker(landmarker=landmarker)

    tracker.release()

    assert landmarker.closed is True
