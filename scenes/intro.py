from core.scene import Scene


class IntroScene(Scene):
    def handle_event(self, event, game_state) -> str | None:
        return None

    def update(self, dt, game_state, services) -> str | None:
        return None

    def draw(self, screen, game_state, services) -> None:
        return None
