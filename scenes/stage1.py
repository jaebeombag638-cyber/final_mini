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

_GHOST_IMAGE_PATH = Path("assets/images/eye.jpg")
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
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            return "stage2"
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None
    #  main.py:109의 
    #  transition = current_scene.update(dt, game_state, services) 에서 
    #  매 프레임 update()가 호출됨. 게임 상태에 따라 화면에 뭘 그릴지 결정하는 함수
    def update(self, dt, game_state, services) -> str | None:
        # 현재 페이즈가 시작된 이후 몇 초 지났는지 누적.
        # dt는 main.py:107 clock.get_time() / 1000로 계산한 직전 프레임과의 시간 차이(초)
        self._phase_elapsed += dt
        # global_rules.py:5의 apply_global_rules() 호출해서 센서 데이터 읽고 rules.py에 넘기기. 
        # rules.py에서 게임 상태 업데이트하고, 장면 전환 필요하면 transition 문자열 반환. 
        # transition이 None이 아니면 그 값이 다음 장면 이름이 됨.
        transition = apply_global_rules(dt, self._phase_elapsed, game_state, services)
        if transition is not None:
            return transition
        # stage1.py:91 호출. 카메라 최신 프레임을 self._last_frame 에 저장.
        self._update_last_frame(services.get("camera"))
        # 인트로 단계면 stage1.py:100 호출.
        if self._phase == _PHASE_INTRO:
            return self._update_intro()

        if self._phase == _PHASE_STARE:
            return self._update_stare()

        if self._phase == _PHASE_JUMPSCARE:
            return self._update_jumpscare(game_state)

        return None
    # main.py가 매 프레임 "지금 화면 그려줘"하고 부르는 함수
    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"): # screen이 진짜 pygame 화면이 맞는지 확인
            return None

        camera = services.get("camera") # sercies에서 camera 객체 가져오기
        screen.fill((0, 0, 0))  # 화면 전체를 검은색으로 채우기 (배경)
        # 인트로 단계면 stage1.py:135 호출
        if self._phase == _PHASE_INTRO:
            self._draw_intro(screen)
        # 눈싸움 단계면 stage1.py:146 호출
        elif self._phase == _PHASE_STARE:
            self._draw_stare(screen, camera)
        # 점프스퀘어 단계면 stage1.py:158 호출    
        elif self._phase == _PHASE_JUMPSCARE:
            self._draw_jumpscare(screen, camera)

        return None

    def _reset(self) -> None: # update()와 draw()에서 쓰는 변수들 전부 초기값으로 되돌리는 함수.
        """장면 상태 초기화 (게임 오버 후 재진입 시에도 호출)."""
        self._phase: str = _PHASE_INTRO # 페이즈를 "intro"로 초기화
        self._phase_elapsed: float = 0.0 # 페이즈 경과 시간 0으로 초기화 
        self._last_frame = None # 카메라 최신 프레임을 저장하는 변수, 처음엔 없으니 None
        self._ghost_img = None # 귀신 눈 이미지, 처음엔 없으니 None
        self._ghost_loaded: bool = False # 귀신 이미지 로드 여부,처음엔 False

    def reset(self) -> None: # main.py def apply_scene_transition()에서 씬 전환 시 next_scene.reset() 호출함. 게임오버 후 stage1으로 돌아올 때 처음부터 다시 시작하게 만드는 함수.
        """장면 재진입 시 처음부터 다시 시작한다."""
        self._reset() # _reset() 함수 호출해서 변수들 초기화

    def _update_last_frame(self, camera) -> None: # update()에서 매 프레임 호출. 저장된 self._last_frame은 _draw_stare()와 _draw_jumpscare()에서 화면에 그릴 때 사용됨.
        if camera is None: # 카메라 없으면 그냥 나감 
            return

        camera.open() # 카메라 열기 (이미 열려있으면 상관X)
        camera_frame = camera.read_frame() # 카메라에서 현재 프레임 읽기
        if not getattr(camera_frame, "is_fallback", False): # 진짜 카메라 프레임일 때만
            self._last_frame = camera_frame.image # 저장 -> draw()의 _draw_stare()와 _draw_jumpscare()에서 이 프레임을 꺼내 화면에 그림.

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

        for i, (text, size) in enumerate(_INTRO_LINES): # 위쪽에 정의된 텍스트 4줄 순서대로
            color = (220, 20, 20) if i == 0 else (185, 185, 185) # 첫 줄만 빨간색, 나머지 회색
            surf = pygame.font.Font(config.FONT_PATH, size).render(text, True, color)
            screen.blit(surf, surf.get_rect(center=(cx, start_y + i * _INTRO_LINE_GAP))) # 화면 중앙에 붙이기 

    def _draw_stare(self, screen: pygame.Surface, camera) -> None:
        """눈싸움 화면: 중앙에 귀신 눈 이미지, 우하단에 사용자 캠."""
        self._load_ghost() # 귀신 눈 이미지 로드 (한 번만)
        if self._ghost_img is not None:
            ghost = pygame.transform.scale(self._ghost_img, _GHOST_IMAGE_SIZE)
            screen.blit( # 화면 중앙에 귀신 눈 이미지 출력
                ghost,
                ghost.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)),
            )

        self._draw_cam_corner(screen, camera) # 우하단에 내 카메라 썸네일 출력

    def _draw_jumpscare(self, screen: pygame.Surface, camera) -> None:
        """점프스케어: 사용자 캠을 전체 화면으로 확대."""
        if self._last_frame is not None and camera is not None:
            surf = camera.to_surface(self._last_frame, pygame) # 저장해둔 마지막 카메라 프레임을 pygame Surface로 변환
            surf = pygame.transform.scale(surf, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)) # 화면 크기로 늘림
            screen.blit(surf, (0, 0)) # 화면 전체에 내 카메라 영상 출력

    def _draw_cam_corner(self, screen: pygame.Surface, camera) -> None:
        """우하단 캠 썸네일을 그린다."""
        if self._last_frame is None or camera is None:
            return
        surf = camera.to_surface(self._last_frame, pygame)
        surf = pygame.transform.scale(surf, _CAMERA_PREVIEW_SIZE)
        x = config.SCREEN_WIDTH - _CAMERA_PREVIEW_SIZE[0] - _CAMERA_PREVIEW_MARGIN
        y = config.SCREEN_HEIGHT - _CAMERA_PREVIEW_SIZE[1] - _CAMERA_PREVIEW_MARGIN
        screen.blit(surf, (x, y))
