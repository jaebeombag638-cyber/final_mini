from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ULTRALYTICS_CONFIG_DIR = PROJECT_ROOT / ".runtime" / "ultralytics"
ULTRALYTICS_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(ULTRALYTICS_CONFIG_DIR))

import config
from core.camera import Camera
from core.detector import Detector


PERSON_BOX_COLOR = (80, 255, 140)
OTHER_BOX_COLOR = (255, 190, 80)
TEXT_COLOR = (255, 255, 255)
WARNING_COLOR = (255, 180, 120)


def main() -> None:
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Your Face YOLO BBox Preview")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 34)
    small_font = pygame.font.Font(None, 24)
    camera = Camera()
    camera.open()
    detector = Detector()
    frame_index = 0

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            frame_index += 1
            camera_frame = camera.read_frame()
            detection_result = detector.detect(camera_frame.image, frame_index)
            surface = camera.to_surface(camera_frame.image)
            surface = pygame.transform.smoothscale(
                surface,
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
            )

            screen.blit(surface, (0, 0))
            _draw_detections(screen, small_font, camera_frame.image, detection_result)
            _draw_status(screen, font, small_font, camera_frame, detection_result)

            pygame.display.flip()
            clock.tick(config.FPS)
    finally:
        detector.release()
        camera.release()
        pygame.quit()


def _draw_detections(screen, font, frame, detection_result) -> None:
    import pygame

    scale_x, scale_y = _calculate_scale(frame, screen.get_size())
    for detection in detection_result.detections:
        x1, y1, x2, y2 = detection.bbox
        rect = pygame.Rect(
            int(x1 * scale_x),
            int(y1 * scale_y),
            int((x2 - x1) * scale_x),
            int((y2 - y1) * scale_y),
        )
        color = PERSON_BOX_COLOR if detection.label == "person" else OTHER_BOX_COLOR
        pygame.draw.rect(screen, color, rect, 3)

        label = f"{detection.label} {detection.confidence:.2f}"
        label_surface = font.render(label, True, color)
        label_y = max(rect.top - 24, 4)
        screen.blit(label_surface, (rect.left, label_y))


def _draw_status(screen, font, small_font, camera_frame, detection_result) -> None:
    person_count = sum(
        1 for detection in detection_result.detections if detection.label == "person"
    )
    status_text = f"사람 bbox: {person_count}개"
    status_color = PERSON_BOX_COLOR if person_count else WARNING_COLOR
    if detection_result.is_fallback:
        status_text = "YOLO fallback: bbox 없음"

    status_surface = font.render(status_text, True, status_color)
    screen.blit(status_surface, (32, 32))

    guide_surface = small_font.render("ESC를 누르면 종료합니다.", True, TEXT_COLOR)
    screen.blit(guide_surface, (32, 72))

    if camera_frame.is_fallback:
        camera_surface = small_font.render(
            "카메라를 열 수 없어 fallback 화면을 표시합니다.",
            True,
            WARNING_COLOR,
        )
        screen.blit(camera_surface, (32, 104))

    if detection_result.error_message:
        error_surface = small_font.render(
            detection_result.error_message,
            True,
            WARNING_COLOR,
        )
        screen.blit(error_surface, (32, 136))


def _calculate_scale(frame, screen_size: tuple[int, int]) -> tuple[float, float]:
    screen_width, screen_height = screen_size
    try:
        frame_height, frame_width = frame.shape[:2]
    except AttributeError:
        frame_height = len(frame)
        frame_width = len(frame[0]) if frame_height else screen_width

    if frame_width == 0 or frame_height == 0:
        return 1.0, 1.0

    return screen_width / frame_width, screen_height / frame_height


if __name__ == "__main__":
    main()
