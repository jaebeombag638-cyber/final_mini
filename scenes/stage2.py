import pygame

import config
from core.scene import Scene
from scenes.global_rules import apply_global_rules


class Stage2Scene(Scene):
    def __init__(self) -> None:
        self._elapsed: float = 0.0

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            return "stage3"
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        self._elapsed += dt
        transition = apply_global_rules(dt, self._elapsed, game_state, services)
        if transition is not None:
            return transition
        if self._elapsed >= config.STAGE_TRANSITION_SECONDS:
            return "stage3"
        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"):
            return None

        screen.fill((0, 0, 0))
        font = pygame.font.Font(config.FONT_PATH, 96)
        text = font.render("STAGE 2", True, (255, 255, 255))
        screen.blit(
            text,
            text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)),
        )
        return None
