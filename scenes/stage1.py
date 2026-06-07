import pygame

import config
from core.scene import Scene


class Stage1Scene(Scene):
    def __init__(self) -> None:
        self._elapsed: float = 0.0

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            return "stage2"
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"):
            return None

        screen.fill((0, 0, 0))
        font = pygame.font.Font(config.FONT_PATH, 96)
        text = font.render("STAGE 1", True, (255, 255, 255))
        screen.blit(
            text,
            text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)),
        )
        return None
