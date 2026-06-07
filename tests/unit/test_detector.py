from core.detector import Detection, DetectionResult, Detector


class FakeYoloModel:
    def __init__(self, detections_by_call):
        self.detections_by_call = list(detections_by_call)
        self.detect_calls = 0

    def detect(self, frame):
        self.detect_calls += 1
        if not self.detections_by_call:
            return []
        return self.detections_by_call.pop(0)


class FailingYoloModel:
    def detect(self, frame):
        raise RuntimeError("YOLO 오류")


def test_detect_returns_bbox_label_and_confidence():
    model = FakeYoloModel(
        [
            [
                Detection(bbox=(10, 20, 110, 220), label="person", confidence=0.91),
                Detection(bbox=(5, 5, 30, 30), label="chair", confidence=0.5),
            ]
        ]
    )
    detector = Detector(model=model)

    result = detector.detect(frame=object(), frame_index=1)

    assert result == DetectionResult(
        detections=(
            Detection(bbox=(10, 20, 110, 220), label="person", confidence=0.91),
            Detection(bbox=(5, 5, 30, 30), label="chair", confidence=0.5),
        )
    )


def test_detect_reuses_cached_result_inside_frame_interval():
    first_detection = Detection(bbox=(10, 20, 110, 220), label="person", confidence=0.91)
    second_detection = Detection(bbox=(0, 0, 20, 20), label="person", confidence=0.4)
    model = FakeYoloModel([[first_detection], [second_detection]])
    detector = Detector(model=model, detect_every_n_frames=5)

    first_result = detector.detect(frame=object(), frame_index=10)
    cached_result = detector.detect(frame=object(), frame_index=12)

    assert cached_result == first_result
    assert model.detect_calls == 1


def test_detect_runs_again_after_frame_interval():
    first_detection = Detection(bbox=(10, 20, 110, 220), label="person", confidence=0.91)
    second_detection = Detection(bbox=(0, 0, 20, 20), label="person", confidence=0.4)
    model = FakeYoloModel([[first_detection], [second_detection]])
    detector = Detector(model=model, detect_every_n_frames=5)

    detector.detect(frame=object(), frame_index=10)
    result = detector.detect(frame=object(), frame_index=15)

    assert result.detections == (second_detection,)
    assert model.detect_calls == 2


def test_detect_returns_fallback_when_model_raises_error():
    detector = Detector(model=FailingYoloModel())

    result = detector.detect(frame=object(), frame_index=1)

    assert result == DetectionResult(
        detections=(),
        is_fallback=True,
        error_message="YOLO 오류",
    )


def test_get_player_bbox_returns_highest_confidence_person():
    detector = Detector(
        model=FakeYoloModel(
            [
                [
                    Detection(bbox=(0, 0, 20, 20), label="person", confidence=0.4),
                    Detection(bbox=(10, 20, 110, 220), label="person", confidence=0.9),
                    Detection(bbox=(5, 5, 30, 30), label="chair", confidence=0.95),
                ]
            ]
        )
    )

    result = detector.detect(frame=object(), frame_index=1)

    assert detector.get_player_bbox(result) == (10, 20, 110, 220)


def test_get_player_bbox_uses_temporary_bbox_when_person_is_missing():
    detector = Detector(model=FakeYoloModel([[Detection((5, 5, 30, 30), "chair", 0.95)]]))
    result = detector.detect(frame=object(), frame_index=1)

    assert detector.get_player_bbox(result, fallback_bbox=(100, 100, 200, 300)) == (
        100,
        100,
        200,
        300,
    )


def test_make_intro_detections_adds_fake_boxes_to_real_detections():
    real_detection = Detection(bbox=(10, 20, 110, 220), label="person", confidence=0.91)
    fake_detection = Detection(bbox=(300, 40, 380, 180), label="shadow", confidence=0.8)
    detector = Detector(model=FakeYoloModel([[real_detection]]))

    result = detector.detect(frame=object(), frame_index=1)

    assert detector.make_intro_detections(result, [fake_detection]) == (
        real_detection,
        fake_detection,
    )
