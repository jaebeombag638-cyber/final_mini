from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


SceneTransition = str | None
Services = Mapping[str, Any]


class Scene(ABC):
    """Base interface every scene must follow.

    Return the next scene name from handle_event() or update() only when a
    transition is needed. Return None to stay on the current scene. draw() must
    only render to the screen and must not request scene transitions.
    """

    @abstractmethod
    def handle_event(self, event, game_state) -> str | None:
        """Handle one pygame event and optionally return the next scene name."""

    @abstractmethod
    def update(self, dt, game_state, services) -> str | None:
        """Update scene state and optionally return the next scene name."""

    @abstractmethod
    def draw(self, screen, game_state, services) -> None:
        """Draw the scene to the pygame screen."""
