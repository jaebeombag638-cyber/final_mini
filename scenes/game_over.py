import pygame

import config
from core.scene import Scene


class GameOverScene(Scene):
    def __init__(self) -> None:
        self.restart_button_rect = pygame.Rect(
            config.SCREEN_WIDTH // 2 - 120,
            config.SCREEN_HEIGHT // 2 + 90,
            240,
            64,
        )

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "quit"
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._restart(game_state)

        if (
            getattr(event, "type", None) == pygame.MOUSEBUTTONDOWN
            and getattr(event, "button", None) == 1
            and self.restart_button_rect.collidepoint(event.pos)
        ):
            return self._restart(game_state)

        return None

    def update(self, dt, game_state, services) -> str | None:
        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"):
            return None

        screen.fill((0, 0, 0))
        title_font = pygame.font.Font(config.FONT_PATH, 96)
        reason_font = pygame.font.Font(config.FONT_PATH, 36)
        button_font = pygame.font.Font(config.FONT_PATH, 34)

        title = title_font.render("GAME OVER", True, (220, 30, 40))
        reason = reason_font.render(
            f"실패 이유: {game_state.game_over_reason or '알 수 없음'}",
            True,
            (240, 240, 240),
        )

        pygame.draw.rect(
            screen,
            (235, 235, 235),
            self.restart_button_rect,
            border_radius=8,
        )
        pygame.draw.rect(
            screen,
            (90, 90, 90),
            self.restart_button_rect,
            border_radius=8,
            width=2,
        )
        button_text = button_font.render("재시작", True, (20, 20, 20))

        screen.blit(
            title,
            title.get_rect(
                center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 90)
            ),
        )
        screen.blit(
            reason,
            reason.get_rect(
                center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 10)
            ),
        )
        screen.blit(
            button_text,
            button_text.get_rect(center=self.restart_button_rect.center),
        )
        return None

    def _restart(self, game_state) -> str:
        game_state.reset_for_restart()
        game_state.change_scene("stage1")
        return "stage1"
