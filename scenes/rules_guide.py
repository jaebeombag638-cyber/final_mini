import pygame

import config
from core.scene import Scene


_BACKGROUND_COLOR = (12, 12, 12)
_TITLE_COLOR = (255, 255, 255)
_RULE_COLOR = (235, 235, 235)
_HINT_COLOR = (180, 180, 180)


class RulesGuideScene(Scene):
    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            return "stage1"
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"):
            return None

        screen.fill(_BACKGROUND_COLOR)

        title_font = pygame.font.Font(config.FONT_PATH, 72)
        rule_font = pygame.font.Font(config.FONT_PATH, 38)
        hint_font = pygame.font.Font(config.FONT_PATH, 30)

        title = title_font.render("생존을 위한 경고", True, _TITLE_COLOR)
        screen.blit(
            title,
            title.get_rect(center=(config.SCREEN_WIDTH // 2, 140)),
        )

        rules = (
            "소리를 내지 마세요. 그들은 숨소리조차 들을 수 있습니다.",
            "표정을 유지하세요. 두려움을 드러내는 순간 그들은 당신의 육체를 탐내기 시작합니다.",
            "시선을 돌리지 마세요. 얼굴이 화면 밖으로 벗어나면 결계가 무너집니다.",
        )
        for index, text in enumerate(rules):
            rule = rule_font.render(text, True, _RULE_COLOR)
            screen.blit(
                rule,
                rule.get_rect(center=(config.SCREEN_WIDTH // 2, 280 + index * 86)),
            )

        hint = hint_font.render("SPACE: 시작    ESC: 종료", True, _HINT_COLOR)
        screen.blit(
            hint,
            hint.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 90)),
        )
        return None
