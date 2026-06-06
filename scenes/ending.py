import pygame

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
        return None
