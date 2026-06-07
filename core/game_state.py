from dataclasses import dataclass, field


MouthLandmark = tuple[float, float]
MouthLandmarks = tuple[MouthLandmark, ...]


@dataclass
class GameState:
    """게임의 현재 상태를 전부 담는 클래스."""

    current_scene: str = "start"
    baseline_mouth_landmarks: MouthLandmarks | None = None
    current_mouth_landmarks: MouthLandmarks = ()
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

    # 게임 오버 처리
    def enter_game_over(self, reason: str) -> None:
        self.is_game_over = True
        self.current_scene = "game_over"
        self.game_over_reason = reason

    # 엔딩 도달 처리
    def reach_ending(self) -> None:
        self.reached_ending = True
        self.current_scene = "ending"

    # 장면 변경 처리
    def change_scene(self, scene_name: str) -> None:
        self.current_scene = scene_name

    # 입 랜드마크 업데이트
    def update_mouth_landmarks(
        self,
        baseline: MouthLandmarks | None,
        current: MouthLandmarks,
    ) -> None:
        self.baseline_mouth_landmarks = baseline
        self.current_mouth_landmarks = current

    # 오디오 데시벨 업데이트
    def update_audio_db(self, audio_db: float) -> None:
        self.current_audio_db = audio_db

    # 스테이지 clear 처리
    def mark_stage_clear(self, stage: int) -> None:
        self.current_stage = stage
        self.stage_results[stage] = "clear"

    # 스테이지 실패 처리
    def mark_stage_failed(self, stage: int) -> None:
        self.current_stage = stage
        self.stage_results[stage] = "failed"
