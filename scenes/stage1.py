import math
from pathlib import Path

import pygame

import config
from core.scene import Scene
from scenes.global_rules import apply_global_rules


_PHASE_INTRO = "intro"
_PHASE_STARE = "stare"
_PHASE_JUMPSCARE = "jumpscare"

_INTRO_DURATION_SECONDS = 4.0
_STARE_DURATION_SECONDS = 5.0
_JUMPSCARE_DURATION_SECONDS = 3.0
_BLINK_CHECK_INTERVAL_SECONDS = 0.033
_STARE_GRACE_SECONDS = 1.0
_FACE_MISSING_LIMIT_SECONDS = 0.25

_EAR_THRESHOLD = 0.22
_LEFT_EYE_IDX = (33, 160, 158, 133, 153, 144)
_RIGHT_EYE_IDX = (263, 387, 385, 362, 380, 373)
_BLINK_CONFIRM_FRAMES = 2

_GHOST_IMAGE_PATH = Path("assets/images/eye2.jpg")
_GHOST_IMAGE_SIZE = (440, 330)
_CAMERA_PREVIEW_SIZE = (320, 240)
_CAMERA_PREVIEW_MARGIN = 10

_INTRO_LINES = [
    ("나는 그날 그것과 눈이 마주쳤다.", 64),
    ("어둠 속 두 눈은 단 한 번도 깜빡이지 않았다.", 42),
    ("그것이 속삭였다.", 42),
    ('"눈을 감지 마라. 감는 순간, 내가 간다."', 42),
]
_INTRO_LINE_GAP = 76  # 줄 간격 (픽셀)


def _ear(points, idx: tuple) -> float:
    """6개 랜드마크로 Eye Aspect Ratio를 계산한다."""
    eye_points = [(points[i].x, points[i].y) for i in idx]
    vertical_distance = math.dist(eye_points[1], eye_points[5]) + math.dist(
        eye_points[2],
        eye_points[4],
    )
    horizontal_distance = math.dist(eye_points[0], eye_points[3])
    if horizontal_distance <= 0:
        return 0.0
    return vertical_distance / (2.0 * horizontal_distance)


class Stage1Scene(Scene):
    def __init__(self) -> None:
        self._reset()
        self._face_cascade = None
        self._eye_cascade = None

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        self._phase_elapsed += dt
        self._check_elapsed += dt

        transition = apply_global_rules(dt, self._phase_elapsed, game_state, services)
        if transition is not None:
            return transition

        self._update_last_frame(services.get("camera"))

        if self._phase == _PHASE_INTRO:
            return self._update_intro()

        if self._phase == _PHASE_STARE:
            return self._update_stare(dt, game_state, services.get("face_tracker"))

        if self._phase == _PHASE_JUMPSCARE:
            return self._update_jumpscare(dt, game_state, services.get("face_tracker"))

        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"):
            return None

        camera = services.get("camera")
        screen.fill((0, 0, 0))

        if self._phase == _PHASE_INTRO:
            self._draw_intro(screen)
        elif self._phase == _PHASE_STARE:
            self._draw_stare(screen, camera)
        elif self._phase == _PHASE_JUMPSCARE:
            self._draw_jumpscare(screen, camera)

        return None

    def _reset(self) -> None:
        """장면 상태 초기화 (게임 오버 후 재진입 시에도 호출)."""
        self._phase: str = _PHASE_INTRO
        self._phase_elapsed: float = 0.0
        self._check_elapsed: float = 0.0
        self._face_missing_elapsed: float = 0.0
        self._last_frame = None
        self._ghost_img = None
        self._ghost_loaded: bool = False
        self._last_face_ok: bool = True
        self._last_blinked: bool = False
        self._blink_count: int = 0

    def _update_last_frame(self, camera) -> None:
        if camera is None:
            return

        camera.open()
        camera_frame = camera.read_frame()
        if not getattr(camera_frame, "is_fallback", False):
            self._last_frame = camera_frame.image

    def _update_intro(self) -> str | None:
        if self._phase_elapsed >= _INTRO_DURATION_SECONDS:
            self._change_phase(_PHASE_STARE)
        return None

    def _update_stare(self, dt, game_state, face_tracker) -> str | None:
        transition = self._check_face_rules(dt, game_state, face_tracker)
        if transition is not None:
            return transition

        if self._phase_elapsed >= _STARE_DURATION_SECONDS:
            self._change_phase(_PHASE_JUMPSCARE)
        return None

    def _update_jumpscare(self, dt, game_state, face_tracker) -> str | None:
        transition = self._check_face_rules(dt, game_state, face_tracker)
        if transition is not None:
            return transition

        if self._phase_elapsed >= _JUMPSCARE_DURATION_SECONDS:
            game_state.mark_stage_clear(1)
            return "stage2"
        return None

    def _change_phase(self, phase: str) -> None:
        self._phase = phase
        self._phase_elapsed = 0.0

    def _check_face_rules(self, dt, game_state, face_tracker) -> str | None:
        if self._is_stare_warming_up():
            return None
        if face_tracker is None or self._last_frame is None:
            return None

        face_ok, blinked = self._face_and_blink(face_tracker, self._last_frame)
        if not face_ok:
            self._face_missing_elapsed += dt
            if self._face_missing_elapsed >= _FACE_MISSING_LIMIT_SECONDS:
                return self._game_over(game_state, "얼굴이 화면을 벗어났습니다!")
            return None

        self._face_missing_elapsed = 0.0
        if blinked:
            return self._game_over(game_state, "눈을 깜빡였습니다!")
        return None

    def _is_stare_warming_up(self) -> bool:
        return self._phase == _PHASE_STARE and self._phase_elapsed < _STARE_GRACE_SECONDS

    def _game_over(self, game_state, reason: str) -> str:
        game_state.enter_game_over(reason)
        self._reset()
        return "game_over"

    def _face_and_blink(self, face_tracker, frame) -> tuple[bool, bool]:
        """얼굴 감지 + 눈 깜빡임 확인. MediaPipe 우선, 실패 시 OpenCV로 폴백."""
        if self._check_elapsed < _BLINK_CHECK_INTERVAL_SECONDS:
            return self._last_face_ok, self._last_blinked
        self._check_elapsed = 0.0

        result = self._try_mediapipe(face_tracker, frame)
        if result is None:
            result = self._try_opencv(frame)

        self._last_face_ok, self._last_blinked = result
        return result

    def _try_mediapipe(self, face_tracker, frame):
        """MediaPipe로 얼굴+눈 감지. 사용 불가 시 None 반환."""
        try:
            lm = face_tracker._get_landmarker()
            if lm is None:
                return None
            res = lm.detect(frame)
            if not res.face_landmarks:
                return (False, False)
            pts = res.face_landmarks[0]
            avg_ear = (_ear(pts, _LEFT_EYE_IDX) + _ear(pts, _RIGHT_EYE_IDX)) / 2.0
            return (True, avg_ear < _EAR_THRESHOLD)
        except Exception:
            return None

    def _try_opencv(self, frame) -> tuple[bool, bool]:
        """OpenCV Haar Cascade로 얼굴+눈 감지 (cv2 내장 모델, 외부 파일 불필요)."""
        try:
            import cv2

            if self._face_cascade is None:
                self._face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
                )
                self._eye_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_eye.xml",
                )

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            small = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)
            faces = self._face_cascade.detectMultiScale(small, 1.1, 5, minSize=(40, 40))

            if len(faces) == 0:
                self._blink_count = 0
                return (False, False)

            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = x * 2, y * 2, w * 2, h * 2
            eye_roi = gray[y : y + int(h * 0.6), x : x + w]
            eyes = self._eye_cascade.detectMultiScale(eye_roi, 1.1, 3, minSize=(15, 15))

            if len(eyes) == 0:
                self._blink_count += 1
            else:
                self._blink_count = 0

            return (True, self._blink_count >= _BLINK_CONFIRM_FRAMES)
        except Exception:
            return (True, False)

    def _load_ghost(self) -> None:
        """귀신 눈 이미지를 처음 한 번만 로드한다."""
        if not self._ghost_loaded:
            if _GHOST_IMAGE_PATH.exists():
                self._ghost_img = pygame.image.load(str(_GHOST_IMAGE_PATH))
            self._ghost_loaded = True

    def _draw_intro(self, screen: pygame.Surface) -> None:
        """인트로 대사: 화면 중앙에 큼직하게 표시."""
        cx = config.SCREEN_WIDTH // 2
        total_h = len(_INTRO_LINES) * _INTRO_LINE_GAP
        start_y = (config.SCREEN_HEIGHT - total_h) // 2

        for i, (text, size) in enumerate(_INTRO_LINES):
            color = (220, 20, 20) if i == 0 else (185, 185, 185)
            surf = pygame.font.Font(config.FONT_PATH, size).render(text, True, color)
            screen.blit(surf, surf.get_rect(center=(cx, start_y + i * _INTRO_LINE_GAP)))

    def _draw_stare(self, screen: pygame.Surface, camera) -> None:
        """눈싸움 화면: 중앙에 귀신 눈 이미지, 우하단에 사용자 캠."""
        self._load_ghost()
        if self._ghost_img is not None:
            ghost = pygame.transform.scale(self._ghost_img, _GHOST_IMAGE_SIZE)
            screen.blit(
                ghost,
                ghost.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)),
            )

        self._draw_cam_corner(screen, camera)

    def _draw_jumpscare(self, screen: pygame.Surface, camera) -> None:
        """점프스케어: 사용자 캠을 전체 화면으로 확대."""
        if self._last_frame is not None and camera is not None:
            surf = camera.to_surface(self._last_frame, pygame)
            surf = pygame.transform.scale(surf, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            screen.blit(surf, (0, 0))

    def _draw_cam_corner(self, screen: pygame.Surface, camera) -> None:
        """우하단 캠 썸네일을 그린다."""
        if self._last_frame is None or camera is None:
            return
        surf = camera.to_surface(self._last_frame, pygame)
        surf = pygame.transform.scale(surf, _CAMERA_PREVIEW_SIZE)
        x = config.SCREEN_WIDTH - _CAMERA_PREVIEW_SIZE[0] - _CAMERA_PREVIEW_MARGIN
        y = config.SCREEN_HEIGHT - _CAMERA_PREVIEW_SIZE[1] - _CAMERA_PREVIEW_MARGIN
        screen.blit(surf, (x, y))
