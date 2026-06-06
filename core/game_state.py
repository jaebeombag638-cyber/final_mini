from dataclasses import dataclass, field


@dataclass
class GameState:
    """게임의 현재 상태를 전부 담는 클래스."""

    current_scene: str = "start"
    baseline_emotion: str | None = None
    current_emotion: str = "unknown"
    current_audio_db: float = 0.0
    current_stage: int = 0
    is_game_over: bool = False
    reached_ending: bool = False
    game_over_reason: str | None = None
    stage_results: dict[int, str] = field(
        default_factory=lambda: {
            1: "pending",
            2: "pending",
            3: "pending",
        }
    )

    def enter_game_over(self, reason: str) -> None:
        self.is_game_over = True
        self.current_scene = "game_over"
        self.game_over_reason = reason

    def reach_ending(self) -> None:
        self.reached_ending = True
        self.current_scene = "ending"

    def change_scene(self, scene_name: str) -> None:
        self.current_scene = scene_name

    def update_emotion(self, baseline: str | None, current: str) -> None:
        self.baseline_emotion = baseline
        self.current_emotion = current

    def update_audio_db(self, audio_db: float) -> None:
        self.current_audio_db = audio_db

    def mark_stage_clear(self, stage: int) -> None:
        self.current_stage = stage
        self.stage_results[stage] = "clear"

    def mark_stage_failed(self, stage: int) -> None:
        self.current_stage = stage
        self.stage_results[stage] = "failed"
