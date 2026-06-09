import pygame

import config
from core.rules import SOUND_LIMIT_REASON
from core.scene import Scene
from scenes.global_rules import apply_global_rules


_TARGET_TEXT = "나 여기 있어"
_RECORD_SECONDS = 5.0
_INTRO_DURATION_SECONDS = 2.0
_RESULT_DISPLAY_SECONDS = 1.0


class Stage2Scene(Scene):
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """장면 재진입 시 음성 판정 상태를 초기화한다."""
        self._elapsed: float = 0.0
        self.intro_duration: float = _INTRO_DURATION_SECONDS
        self.intro_done: bool = False
        self.progress: float = 0.0
        self.time_elapsed: float = 0.0
        self.time_limit: float = _RECORD_SECONDS
        self.audio_status: str = "RECORDING"
        self.user_spoken_text: str = ""
        self.match_ratio_percent: float = 0.0
        self._pending_game_over_elapsed: float | None = None

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_0:
            return "stage3"
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        self._elapsed += dt

        if self._pending_game_over_elapsed is not None:
            self._pending_game_over_elapsed += dt
            if self._pending_game_over_elapsed >= _RESULT_DISPLAY_SECONDS:
                game_state.enter_game_over(SOUND_LIMIT_REASON)
                return "game_over"
            return None

        if not self.intro_done:
            transition = apply_global_rules(dt, self._elapsed, game_state, services)
            if transition is not None:
                return transition

        if self._elapsed < self.intro_duration:
            return None
        if not self.intro_done:
            self.intro_done = True
            return None

        speech = services.get("speech")
        if speech is None:
            return None

        speech.target_text = _TARGET_TEXT
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
            self.audio_status = "FAILED_MATCH"
            self._pending_game_over_elapsed = 0.0
            return None

        self.audio_status = "PHASE_CLEAR"
        game_state.mark_stage_clear(2)
        return "stage3"

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

        text_str = f"소리를 내지 마세요: '{_TARGET_TEXT}'"
        sub_text = "5초 동안 입력된 소리를 Whisper가 텍스트로 변환합니다."
        bar_color = (0, 180, 255)

        text_color = (200, 0, 0)
        text_surface = font.render(text_str, True, text_color)
        screen.blit(
            text_surface,
            text_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 110)),
        )

        sub_color = (120, 120, 120)
        sub_surface = sub_font.render(sub_text, True, sub_color)
        screen.blit(
            sub_surface,
            sub_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 60)),
        )

        if self.audio_status == "RECORDING":
            status_str = "음성 대기 중: 아무 소리도 내지 마세요."
            status_color = (0, 255, 100)
        elif self.audio_status == "CAPTURING_SPEECH":
            status_str = "목소리 감지됨: 입력을 듣고 있습니다..."
            status_color = (255, 100, 100)
        elif self.audio_status == "ANALYZING":
            status_str = "AI 분석 중: 목소리와 문장의 일치율을 계산하고 있습니다..."
            status_color = (0, 255, 255)
        elif self.audio_status == "FAILED_MATCH":
            status_str = f"실패: 소리가 감지되었습니다. 일치율 {self.match_ratio_percent}%"
            status_color = (255, 50, 50)
        else:
            status_str = f"통과: 감지된 문장이 없습니다. 일치율 {self.match_ratio_percent}%"
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
            f"음성 회피 단계 | 남은 시간: {round(remaining_time, 1)}초",
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
