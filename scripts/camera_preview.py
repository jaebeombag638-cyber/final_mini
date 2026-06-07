from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from core.camera import Camera
from core.face_tracker import FaceTracker


MOUTH_LABELS = (
    "왼쪽 입꼬리",
    "오른쪽 입꼬리",
    "윗입술",
    "아랫입술",
)


def main() -> None:
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Your Face Camera Preview")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    camera = Camera()
    camera.open()
    face_tracker = FaceTracker()

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            camera_frame = camera.read_frame()
            face_result = face_tracker.track(
                frame=camera_frame.image,
                now=pygame.time.get_ticks() / 1000,
            )
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

            status_color = (120, 255, 160) if face_result.face_detected else (255, 180, 120)
            status_text = "얼굴 감지됨" if face_result.face_detected else "얼굴 미감지"
            if face_result.is_fallback:
                status_text = "얼굴 추적 fallback"

            status_surface = font.render(status_text, True, status_color)
            screen.blit(status_surface, (32, 32 if not camera_frame.is_fallback else 76))

            if face_result.error_message:
                error_surface = small_font.render(
                    face_result.error_message,
                    True,
                    (255, 180, 120),
                )
                screen.blit(error_surface, (32, 72 if not camera_frame.is_fallback else 116))

            _draw_mouth_landmarks(
                screen,
                small_font,
                face_tracker.last_raw_mouth_landmarks,
                face_result.mouth_landmarks,
            )

            pygame.display.flip()
            clock.tick(config.FPS)
    finally:
        face_tracker.release()
        camera.release()
        pygame.quit()


def _draw_mouth_landmarks(screen, font, raw_landmarks, normalized_landmarks) -> None:
    import pygame

    if not raw_landmarks or not normalized_landmarks:
        return

    width, height = screen.get_size()
    for index, (label, raw_landmark, normalized_landmark) in enumerate(
        zip(MOUTH_LABELS, raw_landmarks, normalized_landmarks)
    ):
        pixel_position = (
            int(raw_landmark[0] * width),
            int(raw_landmark[1] * height),
        )
        pygame_color = (255, 70, 70) if index < 2 else (70, 190, 255)
        pygame.draw.circle(screen, pygame_color, pixel_position, 7)

        text = font.render(
            f"{label}: ({normalized_landmark[0]:.3f}, {normalized_landmark[1]:.3f})",
            True,
            (255, 255, 255),
        )
        screen.blit(text, (32, 120 + index * 28))


if __name__ == "__main__":
    main()
