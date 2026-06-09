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


class Stage1Scene(Scene):
    def __init__(self) -> None:
        self._reset()

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        self._phase_elapsed += dt

        transition = apply_global_rules(dt, self._phase_elapsed, game_state, services)
        if transition is not None:
            return transition

        self._update_last_frame(services.get("camera"))

        if self._phase == _PHASE_INTRO:
            return self._update_intro()

        if self._phase == _PHASE_STARE:
            return self._update_stare()

        if self._phase == _PHASE_JUMPSCARE:
            return self._update_jumpscare(game_state)

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
        self._last_frame = None
        self._ghost_img = None
        self._ghost_loaded: bool = False

    def reset(self) -> None:
        """장면 재진입 시 처음부터 다시 시작한다."""
        self._reset()

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

    def _update_stare(self) -> str | None:
        if self._phase_elapsed >= _STARE_DURATION_SECONDS:
            self._change_phase(_PHASE_JUMPSCARE)
        return None

    def _update_jumpscare(self, game_state) -> str | None:
        if self._phase_elapsed >= _JUMPSCARE_DURATION_SECONDS:
            game_state.mark_stage_clear(1)
            return "stage2"
        return None

    def _change_phase(self, phase: str) -> None:
        self._phase = phase
        self._phase_elapsed = 0.0

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
