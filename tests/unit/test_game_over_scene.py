from types import SimpleNamespace

import pygame

from core.game_state import GameState
from scenes.game_over import GameOverScene


def mouse_click_event(pos: tuple[int, int]) -> SimpleNamespace:
    return SimpleNamespace(type=pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def keydown_event(key: int) -> SimpleNamespace:
    return SimpleNamespace(type=pygame.KEYDOWN, key=key)


def test_restart_button_click_resets_game_and_moves_to_stage1():
    scene = GameOverScene()
    game_state = GameState(current_scene="game_over")
    game_state.enter_game_over("sound_limit")

    transition = scene.handle_event(
        mouse_click_event(scene.restart_button_rect.center),
        game_state,
    )

    assert transition == "stage1"
    assert game_state.current_scene == "stage1"
    assert game_state.is_game_over is False
    assert game_state.game_over_reason is None


def test_enter_key_restarts_game_over_scene():
    scene = GameOverScene()
    game_state = GameState(current_scene="game_over")
    game_state.enter_game_over("face_missing")

    transition = scene.handle_event(keydown_event(pygame.K_RETURN), game_state)

    assert transition == "stage1"
    assert game_state.is_game_over is False


def test_escape_key_requests_quit_from_game_over_scene():
    scene = GameOverScene()

    assert scene.handle_event(keydown_event(pygame.K_ESCAPE), GameState()) == "quit"


def test_draw_renders_game_over_reason_and_restart_button(monkeypatch):
    rendered_texts = []
    blits = []

    class FakeFont:
        def __init__(self, path, size):
            self.path = path
            self.size = size

        def render(self, text, antialias, color):
            rendered_texts.append(text)
            return SimpleNamespace(get_rect=lambda **kwargs: kwargs)

    class FakeScreen:
        def fill(self, color):
            self.fill_color = color

        def blit(self, surface, rect):
            blits.append((surface, rect))

    class FakeDraw:
        @staticmethod
        def rect(screen, color, rect, border_radius=0, width=0):
            screen.last_rect = (color, rect, border_radius, width)

    monkeypatch.setattr(pygame.font, "Font", FakeFont)
    monkeypatch.setattr(pygame.draw, "rect", FakeDraw.rect)

    game_state = GameState(game_over_reason="sound_limit")

    GameOverScene().draw(FakeScreen(), game_state, services={})

    assert "GAME OVER" in rendered_texts
    assert "sound_limit" in rendered_texts
    assert "재시작" in rendered_texts
    assert len(blits) == 3
