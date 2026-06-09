from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import config


BBox = tuple[int, int, int, int]


@dataclass(frozen=True)
class Detection:
    """YOLO 감지 결과 하나를 게임에서 쓰기 쉬운 형태로 담는다."""

    bbox: BBox
    label: str
    confidence: float


@dataclass(frozen=True)
class DetectionResult:
    """객체 감지 결과와 fallback 여부를 함께 담는다."""

    detections: tuple[Detection, ...]
    is_fallback: bool = False
    error_message: str | None = None


class Detector:
    """YOLO 객체 감지를 Stage 3 충돌 판정용 bbox로 변환한다."""

    def __init__(
        self,
        model: Any | None = None,
        model_factory: Any | None = None,
        model_name: str = config.YOLO_MODEL_NAME,
        detect_every_n_frames: int = config.YOLO_DETECT_EVERY_N_FRAMES,
    ) -> None:
        self.model = model
        self.model_factory = model_factory
        self.model_name = model_name
        self.detect_every_n_frames = max(detect_every_n_frames, 1)
        self._last_detected_frame: int | None = None
        self._last_result: DetectionResult | None = None
        self._load_error_message: str | None = None

    def detect(
        self,
        frame,
        frame_index: int,
        use_cache: bool = True,
    ) -> DetectionResult:
        if use_cache and self._should_use_cache(frame_index):
            return self._last_result

        model = self._get_model()
        if model is None:
            return self._cache_result(
                DetectionResult(
                    detections=(),
                    is_fallback=True,
                    error_message=self._load_error_message,
                ),
                frame_index,
            )

        try:
            detections = tuple(model.detect(frame))
        except Exception as error:
            return self._cache_result(
                DetectionResult(
                    detections=(),
                    is_fallback=True,
                    error_message=str(error),
                ),
                frame_index,
            )

        return self._cache_result(DetectionResult(detections=detections), frame_index)

    def get_player_bbox(
        self,
        result: DetectionResult,
        fallback_bbox: BBox | None = None,
    ) -> BBox | None:
        people = [
            detection
            for detection in result.detections
            if detection.label == "person"
        ]
        if not people:
            return fallback_bbox

        return max(people, key=lambda detection: detection.confidence).bbox

    def make_intro_detections(
        self,
        result: DetectionResult,
        fake_detections: Iterable[Detection] = (),
    ) -> tuple[Detection, ...]:
        return (*result.detections, *tuple(fake_detections))

    def release(self) -> None:
        if self.model is not None and hasattr(self.model, "close"):
            self.model.close()
        self.model = None

    def _should_use_cache(self, frame_index: int) -> bool:
        return (
            self._last_result is not None
            and self._last_detected_frame is not None
            and frame_index - self._last_detected_frame < self.detect_every_n_frames
        )

    def _cache_result(
        self,
        result: DetectionResult,
        frame_index: int,
    ) -> DetectionResult:
        self._last_result = result
        self._last_detected_frame = frame_index
        return result

    def _get_model(self):
        if self.model is not None:
            return self.model

        try:
            factory = self.model_factory or self._create_default_model
            self.model = factory()
        except Exception as error:
            self._load_error_message = str(error)
            self.model = None

        return self.model

    def _create_default_model(self):
        return UltralyticsYoloAdapter(self.model_name)


class UltralyticsYoloAdapter:
    """ultralytics YOLO 호출부를 Detector에서 분리한다."""

    def __init__(self, model_name: str) -> None:
        yolo = self._import_yolo()
        self._model = yolo(model_name)

    def detect(self, frame) -> tuple[Detection, ...]:
        results = self._model(frame, verbose=False)
        detections: list[Detection] = []
        for result in results:
            names = result.names
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            for box in boxes:
                xyxy = box.xyxy[0].tolist()
                class_id = int(box.cls[0])
                confidence = round(float(box.conf[0]), 4)
                detections.append(
                    Detection(
                        bbox=tuple(int(value) for value in xyxy),
                        label=str(names[class_id]),
                        confidence=confidence,
                    )
                )

        return tuple(detections)

    def _import_yolo(self):
        from ultralytics import YOLO

        return YOLO
