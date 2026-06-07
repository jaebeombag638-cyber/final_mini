from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from core.audio import AudioMeter


def main() -> None:
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((640, 240))
    pygame.display.set_caption("Your Face Audio Quit Preview")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 26)
    audio = AudioMeter(threshold_db=config.AUDIO_LIMIT_DB)
    audio.start()

    try:
        running = True
        latest_db = 0.0
        is_fallback = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            audio_level = audio.read_db()
            latest_db = audio_level.db
            is_fallback = audio_level.is_fallback
            if audio.is_over_threshold(latest_db):
                running = False

            screen.fill((20, 22, 26))
            db_text = font.render(
                f"현재 소리: {latest_db:.1f} dB",
                True,
                (255, 255, 255),
            )
            threshold_text = small_font.render(
                f"종료 기준: {config.AUDIO_LIMIT_DB:.1f} dB",
                True,
                (190, 196, 205),
            )
            guide_text = small_font.render(
                "큰 소리를 내면 창이 자동으로 닫힙니다. ESC로도 종료할 수 있습니다.",
                True,
                (190, 196, 205),
            )
            fallback_text = small_font.render(
                "마이크 입력을 읽지 못해 fallback 값이 표시됩니다.",
                True,
                (255, 170, 120),
            )

            screen.blit(db_text, (32, 36))
            screen.blit(threshold_text, (32, 86))
            screen.blit(guide_text, (32, 128))
            if is_fallback:
                screen.blit(fallback_text, (32, 170))

            pygame.display.flip()
            clock.tick(config.FPS)
    finally:
        audio.release()
        pygame.quit()


if __name__ == "__main__":
    main()
