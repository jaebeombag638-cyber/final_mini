from core.camera import CameraFrame
from core.detector import Detection, DetectionResult
from scenes.intro import IntroScene


class FakeCamera:
    def __init__(self, frame):
        self.frame = frame
        self.opened = False

    def open(self):
        self.opened = True

    def read_frame(self):
        return CameraFrame(self.frame)


class FakeDetector:
    def __init__(self, detection_result):
        self.detection_result = detection_result
        self.detect_calls = []

    def detect(self, frame, frame_index):
        self.detect_calls.append((frame, frame_index))
        return self.detection_result

    def get_player_bbox(self, result, fallback_bbox=None):
        people = [
            detection
            for detection in result.detections
            if detection.label == "person"
        ]
        if not people:
            return fallback_bbox
        return max(people, key=lambda detection: detection.confidence).bbox


def test_intro_scene_uses_yolo_person_bbox_for_player_box():
    frame = [[(0, 0, 0) for _ in range(640)] for _ in range(480)]
    detector = FakeDetector(
        DetectionResult(
            detections=(
                Detection((10, 20, 110, 220), "person", 0.9),
                Detection((1, 2, 3, 4), "chair", 0.8),
            )
        )
    )
    scene = IntroScene()

    transition = scene.update(
        dt=0.016,
        game_state=object(),
        services={"camera": FakeCamera(frame), "detector": detector},
    )

    assert transition is None
    assert detector.detect_calls == [(frame, 1)]
    assert scene._player_box == (1060, 30, 200, 300)


def test_intro_scene_moves_to_rules_guide_after_duration():
    scene = IntroScene()

    transition = scene.update(dt=10.0, game_state=object(), services={})

    assert transition == "rules_guide"
