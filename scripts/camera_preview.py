from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from core.camera import Camera


def main() -> None:
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Your Face Camera Preview")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    camera = Camera()
    camera.open()

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            camera_frame = camera.read_frame()
            surface = camera.to_surface(camera_frame.image)
            surface = pygame.transform.smoothscale(
                surface,
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
            )

            screen.blit(surface, (0, 0))
            if camera_frame.is_fallback:
                message = font.render(
                    "카메라를 열 수 없어 fallback 화면을 표시합니다.",
                    True,
                    (255, 255, 255),
                )
                screen.blit(message, (32, 32))

            pygame.display.flip()
            clock.tick(config.FPS)
    finally:
        camera.release()
        pygame.quit()


if __name__ == "__main__":
    main()
