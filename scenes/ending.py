import pygame

import config
from core.scene import Scene


class EndingScene(Scene):
    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key in (
            pygame.K_SPACE,
            pygame.K_ESCAPE,
        ):
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"):
            return None

        screen.fill((0, 0, 0))
        font = pygame.font.Font(config.FONT_PATH, 96)
        text = font.render("Ending", True, (255, 255, 255))
        screen.blit(
            text,
            text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)),
        )
        return None
