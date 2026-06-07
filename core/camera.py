from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import config


@dataclass(frozen=True)
class CameraFrame:
    """카메라에서 읽은 프레임과 fallback 여부를 함께 담는다."""

    image: Any
    is_fallback: bool = False


class Camera:
    """OpenCV 웹캠 입력을 pygame에서 재사용하기 쉽게 감싼 클래스."""

    def __init__(
        self,
        camera_index: int = config.CAMERA_INDEX,
        flip_horizontal: bool = True,
        capture_factory: Callable[[int], Any] | None = None,
        fallback_size: tuple[int, int] = (640, 480),
    ) -> None:
        self.camera_index = camera_index
        self.flip_horizontal = flip_horizontal
        self.capture_factory = capture_factory
        self.fallback_size = fallback_size
        self._capture = None

    @property
    def is_opened(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def open(self) -> bool:
        if self._capture is None:
            self._capture = self._create_capture()
        return self.is_opened

    def read_frame(self) -> CameraFrame:
        if not self.is_opened:
            return CameraFrame(self._create_fallback_frame(), is_fallback=True)

        success, frame = self._capture.read()
        if not success or frame is None:
            return CameraFrame(self._create_fallback_frame(), is_fallback=True)

        if self.flip_horizontal:
            frame = self._flip_frame(frame)

        return CameraFrame(frame)

    def to_surface(self, bgr_frame, pygame_module=None):
        pygame = pygame_module or self._import_pygame()
        rgb_frame = self._convert_bgr_to_rgb(bgr_frame)
        if hasattr(rgb_frame, "swapaxes"):
            rgb_frame = rgb_frame.swapaxes(0, 1)
        return pygame.surfarray.make_surface(rgb_frame)

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _create_capture(self):
        if self.capture_factory is not None:
            return self.capture_factory(self.camera_index)

        cv2 = self._import_cv2()
        return cv2.VideoCapture(self.camera_index)

    def _create_fallback_frame(self):
        width, height = self.fallback_size
        try:
            np = self._import_numpy()
        except ImportError:
            return [[(40, 40, 40) for _ in range(width)] for _ in range(height)]

        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = (40, 40, 40)
        return frame

    def _flip_frame(self, frame):
        try:
            return frame[:, ::-1]
        except TypeError:
            return [list(reversed(row)) for row in frame]

    def _convert_bgr_to_rgb(self, bgr_frame):
        try:
            return bgr_frame[:, :, ::-1]
        except TypeError:
            return [
                [[pixel[2], pixel[1], pixel[0]] for pixel in row]
                for row in bgr_frame
            ]

    def _import_cv2(self):
        import cv2

        return cv2

    def _import_numpy(self):
        import numpy as np

        return np

    def _import_pygame(self):
        import pygame

        return pygame
