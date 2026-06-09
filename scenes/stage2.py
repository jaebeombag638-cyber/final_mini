import pygame

import config
from core.rules import SOUND_LIMIT_REASON
from core.scene import Scene
from scenes.global_rules import apply_global_rules


_PHASE_TARGETS = (
    "나 여기 있어",
    "내가 보이지 않니",
    "살고 싶다면 지금 당장 소리 내어 읽으세요",
)
_RECORD_SECONDS = 10.0
_INTRO_DURATION_SECONDS = 1.0


class Stage2Scene(Scene):
    def __init__(self) -> None:
        self._elapsed: float = 0.0
        self._phase_index: int = 0
        self.intro_duration: float = _INTRO_DURATION_SECONDS
        self.intro_done: bool = False
        self.current_phase: int = 1
        self.progress: float = 0.0
        self.time_elapsed: float = 0.0
        self.time_limit: float = _RECORD_SECONDS
        self.audio_status: str = "RECORDING"
        self.user_spoken_text: str = ""
        self.match_ratio_percent: float = 0.0

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        self._elapsed += dt
        transition = apply_global_rules(dt, self._elapsed, game_state, services)
        if transition is not None:
            return transition

        if self._elapsed < self.intro_duration:
            return None
        self.intro_done = True

        speech = services.get("speech")
        if speech is None:
            return None

        target_text = _PHASE_TARGETS[self._phase_index]
        speech.target_text = target_text
        self.audio_status = "RECORDING"
        self.time_elapsed = 0.0
        self.progress = 0.0

        self.audio_status = "ANALYZING"
        result = speech.recognize(_RECORD_SECONDS)
        self.time_elapsed = self.time_limit
        self.progress = 100.0
        self.user_spoken_text = result.recognized_text.strip() or "(판독 불가)"
        self.match_ratio_percent = round(result.similarity * 100.0, 1)

        if self.user_spoken_text != "(판독 불가)":
            game_state.enter_game_over(SOUND_LIMIT_REASON)
            self.audio_status = "FAILED_MATCH"
            return "game_over"

        self.audio_status = "PHASE_CLEAR"
        if self._phase_index == len(_PHASE_TARGETS) - 1:
            game_state.mark_stage_clear(2)
            return "stage3"

        self._phase_index += 1
        self.current_phase = self._phase_index + 1
        self.time_elapsed = 0.0
        self.progress = 0.0
        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"):
            return None

        screen.fill((0, 0, 0))

        if not self.intro_done:
            font = pygame.font.Font(config.FONT_PATH, 96)
            text = font.render("STAGE 2", True, (255, 255, 255))
            screen.blit(
                text,
                text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)),
            )
            return None

        font = pygame.font.Font(config.FONT_PATH, 38)
        sub_font = pygame.font.Font(config.FONT_PATH, 22)
        phase_font = pygame.font.Font(config.FONT_PATH, 26)
        status_font = pygame.font.Font(config.FONT_PATH, 26)
        debug_font = pygame.font.Font(config.FONT_PATH, 22)

        if self.current_phase == 1:
            text_str = "화면의 대사를 소리 내어 읽으세요: '나 여기 있어'"
            sub_text = "제한 시간 내에 또박또박 대사를 완독해야 합니다."
            bar_color = (0, 180, 255)
        elif self.current_phase == 2:
            text_str = "더욱 또렷하게 읽으세요: '내가 보이지 않니'"
            sub_text = "발음이 부정확하면 일치율이 오르지 않습니다."
            bar_color = (255, 165, 0)
        else:
            text_str = "마지막 문장: '살고 싶다면 지금 당장 소리 내어 읽으세요'"
            sub_text = "시간이 없습니다. 당장 크게 소리내어 읽어!!!"
            bar_color = (255, 0, 0)

        text_color = (255, 255, 0) if self.current_phase == 3 else (200, 0, 0)
        text_surface = font.render(text_str, True, text_color)
        screen.blit(
            text_surface,
            text_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 110)),
        )

        sub_color = (255, 0, 0) if self.current_phase == 3 else (120, 120, 120)
        sub_surface = sub_font.render(sub_text, True, sub_color)
        screen.blit(
            sub_surface,
            sub_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 60)),
        )

        if self.audio_status == "RECORDING":
            status_str = "🟢 [ 음성 대기 중 ] 제한 시간 내에 대사를 읽어주세요."
            status_color = (0, 255, 100)
        elif self.audio_status == "CAPTURING_SPEECH":
            status_str = "🔴 [ 목소리 감지됨 ] 대사를 끝까지 듣고 있습니다..."
            status_color = (255, 100, 100)
        elif self.audio_status == "ANALYZING":
            status_str = "🤖 [ AI 분석 중 ] 목소리와 문장을 채점하고 있습니다..."
            status_color = (0, 255, 255)
        elif self.audio_status == "FAILED_MATCH":
            status_str = f"⚠️ [ 실패 ] 일치율 50% 미달. 다시 읽으세요! ({self.match_ratio_percent}%)"
            status_color = (255, 50, 50)
        else:
            status_str = f"✅ [ 통과 ] 일치율 {self.match_ratio_percent}% 달성! 다음 단계로..."
            status_color = (0, 255, 0)

        status_surface = status_font.render(status_str, True, status_color)
        screen.blit(
            status_surface,
            status_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 15)),
        )

        spoken_display = (
            f"AI 인식 문장: \"{self.user_spoken_text}\"  |  "
            f"현재 일치율: {self.match_ratio_percent}%"
        )
        result_color = (180, 180, 180) if self.match_ratio_percent < 50.0 else (100, 255, 100)
        result_surface = debug_font.render(spoken_display, True, result_color)
        screen.blit(
            result_surface,
            result_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 35)),
        )

        remaining_time = max(0.0, self.time_limit - self.time_elapsed)
        phase_surface = phase_font.render(
            f"음성 돌파 단계 [ {self.current_phase} / 3 ]  |  남은 시간: {round(remaining_time, 1)}초",
            True,
            (255, 255, 255),
        )
        screen.blit(
            phase_surface,
            phase_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 75)),
        )

        bar_width, bar_height = 500, 20
        bar_x = (config.SCREEN_WIDTH - bar_width) // 2
        bar_y = (config.SCREEN_HEIGHT // 2) + 110
        pygame.draw.rect(screen, (70, 70, 70), (bar_x, bar_y, bar_width, bar_height), 2)
        fill_width = int(bar_width * (self.progress / 100.0))
        if fill_width > 0:
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_width, bar_height))
        return None
