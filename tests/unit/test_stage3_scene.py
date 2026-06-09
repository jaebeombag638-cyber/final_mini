from scenes.stage3 import Stage3Scene
from core.detector import Detection, DetectionResult


class FakeCamera:
    mirror_display = False

    def __init__(self) -> None:
        self.frames = [
            [[0 for _ in range(640)] for _ in range(480)],
            [[0 for _ in range(640)] for _ in range(480)],
        ]
        self.index = 0

    def open(self) -> bool:
        return True

    def read_frame(self):
        frame = self.frames[self.index]
        self.index += 1
        return type("CameraFrame", (), {"image": frame})()


class FakeDetector:
    def __init__(self) -> None:
        self.detect_calls = []
        self.bboxes = [
            (100, 100, 200, 300),
            (200, 100, 300, 300),
        ]

    def detect(self, frame, frame_index: int, use_cache: bool = True):
        self.detect_calls.append((frame_index, use_cache))
        bbox = self.bboxes[len(self.detect_calls) - 1]
        return DetectionResult((Detection(bbox, "person", 1.0),))

    def get_player_bbox(self, result, fallback_bbox=None):
        return result.detections[0].bbox


def test_stage3_scales_player_bbox_to_screen_coordinates():
    scene = Stage3Scene()
    frame = [[0 for _ in range(640)] for _ in range(480)]

    bbox = scene._scale_bbox_to_screen(
        bbox=(160, 120, 320, 360),
        frame=frame,
        mirror_display=False,
    )

    assert bbox == (320, 180, 640, 540)


def test_stage3_scales_mirrored_player_bbox_to_screen_coordinates():
    scene = Stage3Scene()
    frame = [[0 for _ in range(640)] for _ in range(480)]

    bbox = scene._scale_bbox_to_screen(
        bbox=(160, 120, 320, 360),
        frame=frame,
        mirror_display=True,
    )

    assert bbox == (640, 180, 960, 540)


def test_stage3_updates_player_hitbox_without_detector_cache():
    scene = Stage3Scene()
    camera = FakeCamera()
    detector = FakeDetector()
    services = {
        "camera": camera,
        "detector": detector,
    }

    scene.update(0.1, game_state=object(), services=services)
    first_hitbox = scene.player_hitbox
    scene.update(0.1, game_state=object(), services=services)

    assert detector.detect_calls == [(1, False), (2, False)]
    assert scene.player_hitbox != first_hitbox
