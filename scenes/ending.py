import math
import random

import pygame

import config
from core.scene import Scene

_FILTER_DELAY = 1.0   # 메시지 표시 후 필터 적용까지 대기(초)
_ZOOM_DELAY = 2.0     # 필터 적용 1초 후 줌 시작
_ZOOM_TARGET = 5.0
_ZOOM_SPEED = 3.0     # 초당 줌 배율 증가량

_BACKGROUND_COLOR = (0, 0, 0)
_TEXT_COLOR = (255, 255, 255)
_SMILE_COLOR = (0, 220, 0)
_EYE_COLOR = (255, 0, 0)


def _draw_creepy_filter(
    surface: pygame.Surface,
    raw_mouth_landmarks: tuple,
    sw: int,
    sh: int,
) -> None:
    """입 랜드마크 기반으로 으스스한 스마일 필터를 그린다."""
    if len(raw_mouth_landmarks) < 4:
        return

    def to_px(point: tuple) -> tuple[int, int]:
        return (int(point[0] * sw), int(point[1] * sh))

    left_corner = to_px(raw_mouth_landmarks[0])
    right_corner = to_px(raw_mouth_landmarks[1])
    upper_lip = to_px(raw_mouth_landmarks[2])
    lower_lip = to_px(raw_mouth_landmarks[3])

    mouth_cx = (left_corner[0] + right_corner[0]) // 2
    mouth_cy = (upper_lip[1] + lower_lip[1]) // 2
    mouth_w = abs(right_corner[0] - left_corner[0])
    face_r = max(mouth_w, 40)

    # 얼굴 중심 (입 위치 기준으로 근사)
    face_cx = mouth_cx
    face_cy = mouth_cy - face_r

    # 눈 위치 근사 (입 너비 기준)
    eye_offset_x = mouth_w // 3
    eye_offset_y = face_r // 2
    left_eye = (face_cx - eye_offset_x, face_cy - eye_offset_y)
    right_eye = (face_cx + eye_offset_x, face_cy - eye_offset_y)

    # X 모양 눈
    eye_r = max(face_r // 8, 12)
    for ex, ey in (left_eye, right_eye):
        pygame.draw.line(surface, _EYE_COLOR, (ex - eye_r, ey - eye_r), (ex + eye_r, ey + eye_r), 4)
        pygame.draw.line(surface, _EYE_COLOR, (ex + eye_r, ey - eye_r), (ex - eye_r, ey + eye_r), 4)

    # 넓게 퍼진 으스스한 미소 호
    smile_w = mouth_w + face_r // 3
    smile_h = face_r // 2
    smile_rect = pygame.Rect(
        mouth_cx - smile_w // 2,
        mouth_cy - smile_h // 4,
        smile_w,
        smile_h,
    )
    pygame.draw.arc(surface, _SMILE_COLOR, smile_rect, math.pi, 2 * math.pi, 4)


class EndingScene(Scene):
    def __init__(self) -> None:
        self._last_frame = None
        self._elapsed: float = 0.0
        self._zoom: float = 1.0
        self._raw_mouth_landmarks: tuple = ()

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key in (
            pygame.K_SPACE,
            pygame.K_ESCAPE,
        ):
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
        if not frame.is_fallback:
            self._last_frame = frame.image

            # 필터 적용 단계부터 얼굴 추적
            if self._elapsed >= _FILTER_DELAY:
                face_tracker.track(frame.image, self._elapsed)
                self._raw_mouth_landmarks = face_tracker.last_raw_mouth_landmarks

        if self._elapsed >= _ZOOM_DELAY:
            self._zoom = min(_ZOOM_TARGET, self._zoom + _ZOOM_SPEED * dt)

        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"):
            return None

        sw, sh = config.SCREEN_WIDTH, config.SCREEN_HEIGHT

        # 카메라 화면 (감지 박스 없음)
        camera = services.get("camera")
        if self._last_frame is not None and camera is not None:
            surface = camera.to_surface(self._last_frame, pygame)
            surface = pygame.transform.scale(surface, (sw, sh))

            # 줌: surface를 확대한 뒤 중앙을 잘라서 표시
            if self._zoom > 1.0:
                zoomed_w = int(sw * self._zoom)
                zoomed_h = int(sh * self._zoom)
                zoomed = pygame.transform.scale(surface, (zoomed_w, zoomed_h))
                x_offset = (zoomed_w - sw) // 2
                y_offset = (zoomed_h - sh) // 2
                screen.blit(zoomed, (0, 0), (x_offset, y_offset, sw, sh))
            else:
                screen.blit(surface, (0, 0))
        else:
            screen.fill(_BACKGROUND_COLOR)

        # 으스스한 얼굴 필터
        if self._elapsed >= _FILTER_DELAY and self._raw_mouth_landmarks:
            filter_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            filter_surf.fill((0, 0, 0, 0))
            _draw_creepy_filter(filter_surf, self._raw_mouth_landmarks, sw, sh)
            screen.blit(filter_surf, (0, 0))

        # 축하 메시지
        alpha = min(255, int(self._elapsed * 500))
        font = pygame.font.Font(config.FONT_PATH, 42)
        msg = "축하합니다. 이제 이곳엔 당신 뿐입니다."
        for dx, dy in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            glow = font.render(msg, True, (60, 0, 0))
            glow.set_alpha(alpha)
            screen.blit(glow, glow.get_rect(center=(sw // 2 + dx, sh - 80 + dy)))
        text = font.render(msg, True, _TEXT_COLOR)
        text.set_alpha(alpha)
        screen.blit(text, text.get_rect(center=(sw // 2, sh - 80)))

        return None
