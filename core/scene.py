from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


SceneTransition = str | None   # 타입 정의
Services = Mapping[str, Any]   # 서비스 컨테이너 (각 scene이 필요한 기능을 여기서 갖다 씀)

# 추상 클래스: 틀만 정의하고 실제 구현은 자식 클래스에서
class Scene(ABC):
    """모든 장면이 따라야 하는 기본 인터페이스

    장면 전환이 필요할 때만 handle_event() 또는 update()에서 다음 장면
    이름을 반환한다. 현재 장면을 유지하려면 None을 반환한다. draw()는
    화면 출력만 담당하고 장면 전환을 요청하지 않는다.
    """

    @abstractmethod
    def handle_event(self, event, game_state) -> str | None:
        """pygame 이벤트 하나를 처리하고 필요하면 다음 장면 이름을 반환한다."""

    @abstractmethod
    def update(self, dt, game_state, services) -> str | None:
        """장면 상태를 갱신하고 필요하면 다음 장면 이름을 반환한다."""

    @abstractmethod
    def draw(self, screen, game_state, services) -> None:
        """장면을 pygame 화면에 그린다."""
