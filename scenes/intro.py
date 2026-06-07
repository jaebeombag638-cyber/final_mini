import math
import random

import pygame

import config
from core.detector import DetectionResult
from core.scene import Scene

_FAKE_BOX_COUNT_MIN = 3  # 가짜 박스 최소 개수
_FAKE_BOX_COUNT_MAX = 6  # 가짜 박스 최대 개수
_WIGGLE_AMP_MIN = 3.0  # 가짜 박스 흔들림 최소 진폭
_WIGGLE_AMP_MAX = 10.0  # 가짜 박스 흔들림 최대 진폭
_FAKE_BOX_PLAYER_MARGIN = int(_WIGGLE_AMP_MAX) + 10
_INTRO_DURATION = 10.0

_BACKGROUND_COLOR = (20, 20, 20)
_COLOR_MAIN = (0, 255, 80)
_COLOR_FAKE = (255, 0, 0)
_BOX_THICKNESS = 2


def _make_fake_boxes(count: int, player_rect: pygame.Rect) -> list[dict]:
    """사람 박스와 겹치지 않는 가짜 감지 박스를 생성한다."""
    rng = random.Random()
    player_exclusion = player_rect.inflate(
        _FAKE_BOX_PLAYER_MARGIN * 2,
        _FAKE_BOX_PLAYER_MARGIN * 2,
    )
    strip_width = config.SCREEN_WIDTH // count
    max_box_width = min(200, strip_width - 20)

    boxes = []
    for index in range(count):
        x_min = index * strip_width
        x_max = (index + 1) * strip_width

        for _ in range(200):
            width = rng.randint(min(80, max_box_width), max_box_width)
            height = rng.randint(80, 200)
            x = rng.randint(x_min, max(x_min, x_max - width))
            y = rng.randint(0, max(0, config.SCREEN_HEIGHT - height))
            candidate = pygame.Rect(x, y, width, height)
            if not candidate.colliderect(player_exclusion):
                break

        boxes.append(
            {
                "bx": x,
                "by": y,
                "w": width,
                "h": height,
                "ax": rng.uniform(_WIGGLE_AMP_MIN, _WIGGLE_AMP_MAX),
                "ay": rng.uniform(_WIGGLE_AMP_MIN, _WIGGLE_AMP_MAX),
                "fx": rng.uniform(0.4, 1.8),
                "fy": rng.uniform(0.4, 1.8),
                "px": rng.uniform(0, 2 * math.pi),
                "py": rng.uniform(0, 2 * math.pi),
            }
        )

    return boxes


class IntroScene(Scene):
    def __init__(self) -> None:
        self._last_frame = None
        self._elapsed: float = 0.0
        self._frame_index: int = 0
        self._player_box: tuple[int, int, int, int] | None = None
        self._fake_box_count = random.randint(_FAKE_BOX_COUNT_MIN, _FAKE_BOX_COUNT_MAX)
        self._fake_boxes: list[dict] = []

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            return "stage1"
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        self._elapsed += dt
        if self._elapsed >= _INTRO_DURATION:
            return "stage1"

        camera = services.get("camera")
        detector = services.get("detector")
        if camera is None or detector is None:
            return None

        camera.open()
        camera_frame = camera.read_frame()
        self._last_frame = camera_frame.image
        self._frame_index += 1

        if camera_frame.is_fallback:
            return None

        detection_result = detector.detect(camera_frame.image, self._frame_index)
        self._update_player_box(detector, detection_result, camera_frame.image)
        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"):
            return None

        camera = services.get("camera")
        if self._last_frame is not None and camera is not None:
            surface = camera.to_surface(self._last_frame, pygame)
            surface = pygame.transform.scale(surface, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            screen.blit(surface, (0, 0))
        else:
            screen.fill(_BACKGROUND_COLOR)

        self._draw_detection_boxes(screen)
        return None

    def _update_player_box(self, detector, detection_result: DetectionResult, frame) -> None:
        player_bbox = detector.get_player_bbox(detection_result)
        if player_bbox is None:
            self._player_box = None
            return

        self._player_box = self._scale_bbox(player_bbox, frame)
        if not self._fake_boxes:
            self._fake_boxes = _make_fake_boxes(
                self._fake_box_count,
                pygame.Rect(*self._player_box),
            )

    def _scale_bbox(self, bbox: tuple[int, int, int, int], frame) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = bbox
        frame_width, frame_height = self._get_frame_size(frame)
        scale_x = config.SCREEN_WIDTH / frame_width
        scale_y = config.SCREEN_HEIGHT / frame_height
        return (
            int(x1 * scale_x),
            int(y1 * scale_y),
            int((x2 - x1) * scale_x),
            int((y2 - y1) * scale_y),
        )

    def _get_frame_size(self, frame) -> tuple[int, int]:
        try:
            frame_height, frame_width = frame.shape[:2]
        except AttributeError:
            frame_height = len(frame)
            frame_width = len(frame[0]) if frame_height else config.SCREEN_WIDTH

        return max(frame_width, 1), max(frame_height, 1)

    def _draw_detection_boxes(self, screen: pygame.Surface) -> None:
        for box in self._fake_boxes:
            dx = int(box["ax"] * math.sin(self._elapsed * box["fx"] + box["px"]))
            dy = int(box["ay"] * math.sin(self._elapsed * box["fy"] + box["py"]))
            rect = pygame.Rect(box["bx"] + dx, box["by"] + dy, box["w"], box["h"])
            pygame.draw.rect(screen, _COLOR_FAKE, rect, _BOX_THICKNESS)

        if self._player_box is not None:
            pygame.draw.rect(screen, _COLOR_MAIN, pygame.Rect(*self._player_box), _BOX_THICKNESS)
