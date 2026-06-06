from dataclasses import dataclass


@dataclass
class GameState:
    current_scene: str = "start"
    baseline_emotion: str | None = None
    current_emotion: str = "unknown"
    current_audio_db: float = 0.0
    current_stage: int = 0
    is_game_over: bool = False
    reached_ending: bool = False
    game_over_reason: str | None = None

    def enter_game_over(self, reason: str) -> None:
        self.is_game_over = True
        self.current_scene = "game_over"
        self.game_over_reason = reason

    def reach_ending(self) -> None:
        self.reached_ending = True
        self.current_scene = "ending"
