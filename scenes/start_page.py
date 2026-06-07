from pathlib import Path

import pygame

import config
from core.scene import Scene

_MOUTH_OPEN_RATIO = 0.35  # 입 높이/너비 비율이 이 값 초과 시 입 열림으로 판정
_DETECTION_DELAY = 3.0  # 창 표시 후 입 감지 시작까지 대기 시간(초)
_BACKGROUND_COLOR = (20, 20, 20)
_OVERLAY_COLOR = (0, 0, 0, 120)
_TITLE_COLOR = (255, 255, 255)
_HINT_COLOR = (200, 200, 200)
_KOREAN_FONT_PATH = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "MUNMAK_DALBANCHE.ttf"


class StartPageScene(Scene):
    def __init__(self) -> None:
        self._last_frame = None
        self._elapsed: float = 0.0

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            return "intro"
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        self._elapsed += dt

        camera = services.get("camera")
        face_tracker = services.get("face_tracker")
        if camera is None or face_tracker is None:
            return None

        camera.open()
        frame = camera.read_frame()
        self._last_frame = frame.image

        if frame.is_fallback or self._elapsed < _DETECTION_DELAY:
            return None

        tracking_result = face_tracker.track(frame.image, self._elapsed)
        if tracking_result.face_detected and self._is_mouth_open(tracking_result.mouth_landmarks):
            return "intro"

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

        self._draw_overlay(screen)
        return None

    def _is_mouth_open(self, mouth_landmarks) -> bool:
        if len(mouth_landmarks) < 4:
            return False

        left_corner, right_corner, upper_lip, lower_lip = mouth_landmarks[:4]
        mouth_width = abs(right_corner[0] - left_corner[0])
        mouth_height = abs(lower_lip[1] - upper_lip[1])
        return mouth_width > 0 and mouth_height / mouth_width > _MOUTH_OPEN_RATIO

    def _draw_overlay(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(_OVERLAY_COLOR)
        screen.blit(overlay, (0, 0))

        font_title = pygame.font.Font(_KOREAN_FONT_PATH, 90)
        font_sub = pygame.font.Font(_KOREAN_FONT_PATH, 40)

        title = font_title.render("당신은 지금 혼자 있나요?", True, _TITLE_COLOR)
        screen.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 60)))

        hint = font_sub.render("확실하지 않다면 esc를 누르세요", True, _HINT_COLOR)
        screen.blit(hint, hint.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 40)))
