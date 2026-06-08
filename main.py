import config
from core.audio import AudioMeter
from core.camera import Camera
from core.detector import Detector
from core.face_tracker import FaceTracker
from core.game_state import GameState
from core.rules import GlobalRules
from core.speech import SpeechRecognizer
from scenes.ending import EndingScene
from scenes.game_over import GameOverScene
from scenes.intro import IntroScene
from scenes.stage1 import Stage1Scene
from scenes.stage2 import Stage2Scene
from scenes.stage3 import Stage3Scene
from scenes.start_page import StartPageScene


SERVICE_NAMES = (
    "camera",
    "audio",
    "face_tracker",
    "detector",
    "speech",
    "rules",
)


def create_services() -> dict[str, object | None]:
    return {
        "camera": Camera(),
        "audio": AudioMeter(),
        "face_tracker": FaceTracker(),
        "detector": Detector(),
        "speech": SpeechRecognizer(),
        "rules": GlobalRules(),
    }


def release_services(services: dict[str, object | None]) -> None:
    for service in services.values():
        if service is not None and hasattr(service, "release"):
            service.release()


def create_scenes() -> dict[str, object]:
    return {
        "start": StartPageScene(),
        "intro": IntroScene(),
        "stage1": Stage1Scene(),
        "stage2": Stage2Scene(),
        "stage3": Stage3Scene(),
        "ending": EndingScene(),
        "game_over": GameOverScene(),
    }


def apply_scene_transition(transition: str | None, game_state: GameState) -> bool:
    if transition is None:
        return True
    if transition == "quit":
        return False

    game_state.change_scene(transition)
    return True


def run() -> None:
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Your Face")
    clock = pygame.time.Clock()   # 프레임 제한용 시계
    game_state = GameState()
    services = create_services()
    scenes = create_scenes()

    try:
        running = True
        while running:
            current_scene = scenes[game_state.current_scene]

            for event in pygame.event.get():   # 사용자 입력 이벤트 처리
                if event.type == pygame.QUIT:
                    running = False
                    break

                transition = current_scene.handle_event(event, game_state)
                running = apply_scene_transition(transition, game_state)
                if not running:
                    break

            if not running:
                break

            dt = clock.get_time() / 1000
            current_scene = scenes[game_state.current_scene]
            transition = current_scene.update(dt, game_state, services)
            running = apply_scene_transition(transition, game_state)
            if not running:
                break

            current_scene = scenes[game_state.current_scene]
            screen.fill((0, 0, 0))
            current_scene.draw(screen, game_state, services)
            pygame.display.flip()   # 화면 업데이트 (지금까지 그린 거 출력)
            clock.tick(config.FPS)  # 프레임 제한
    finally:
        release_services(services)
        pygame.quit()


if __name__ == "__main__":
    run()
