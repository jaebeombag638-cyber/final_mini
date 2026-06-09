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
        rule_font = pygame.font.Font(config.FONT_PATH, 28)
        hint_font = pygame.font.Font(config.FONT_PATH, 20)

        title = title_font.render("다행이네요! 아직 살아 계시군요.", True, _TITLE_COLOR)
        screen.blit(
            title,
            title.get_rect(center=(config.SCREEN_WIDTH // 2, 140)),
        )

        rules = (
            "너무 겁먹진 마세요. 제가 당신을 도와드릴게요.",
            "우선 조용히 계셔야 해요. 그들은 아주 예민해서 작은 숨소리도 놓치지 않거든요.",
            "그리고 즐거워도, 무서워도 너무 솔직해지지는 마세요.",
            "배고픈 그들에게 당신이 아직 살아있다는 사실을 알려줄 필요는 없으니까요.",
            "마지막으로 제가 당신을 계속 지켜볼 수 있게 해주세요.",
            "제 시야에서 벗어나는 건 좋은 선택이 아닐걸요?"
        )
        for index, text in enumerate(rules):
            rule = rule_font.render(text, True, _RULE_COLOR)
            screen.blit(
                rule,
                rule.get_rect(center=(config.SCREEN_WIDTH // 2, 280 + index * 60)),
            )

        hint = hint_font.render("SPACE: 시작    ESC: 종료", True, _HINT_COLOR)
        screen.blit(
            hint,
            hint.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 90)),
        )
        return None
