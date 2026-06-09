import pygame

import config
from core.scene import Scene
from scenes.global_rules import apply_global_rules


_GHOST_IMAGE_PATH = "assets/images/miiya-halloween-4451903_640.png"
_GHOST_SIZE = 60
_GHOST_SPEED_X = 120
_GHOST_SPEED_Y = 90
_PLAYER_HITBOX_RATIO = 0.4


class Stage3Scene(Scene):
    def __init__(self) -> None:
        self.player_bbox = None
        self.player_hitbox = None
        self.ghosts = [
            {"bbox": (20, 20, 80, 80), "vx": _GHOST_SPEED_X, "vy": _GHOST_SPEED_Y},
            {
                "bbox": (
                    config.SCREEN_WIDTH - _GHOST_SIZE - 20,
                    config.SCREEN_HEIGHT - _GHOST_SIZE - 20,
                    config.SCREEN_WIDTH - 20,
                    config.SCREEN_HEIGHT - 20,
                ),
                "vx": -_GHOST_SPEED_X,
                "vy": -_GHOST_SPEED_Y,
            },
        ]
        self.survive_time = 0.0
        self.clear_time = config.STAGE3_TIME_LIMIT_SECONDS
        self.frame_index = 0
        self.current_frame = None
        self.ghost_image = None

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            return "ending"
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        self.frame_index += 1
        self.survive_time += dt

        rule_result = apply_global_rules(
            dt=dt,
            now=self.survive_time,
            game_state=game_state,
            services=services,
        )

        if rule_result:
            return rule_result

        camera = services.get("camera")
        detector = services.get("detector")
        if camera is None or detector is None:
            return None

        camera.open()
        camera_frame = camera.read_frame()
        self.current_frame = camera_frame

        detection_result = detector.detect(
            camera_frame.image,
            self.frame_index,
        )

        detected_bbox = detector.get_player_bbox(
            detection_result,
            fallback_bbox=None,
        )

        if detected_bbox is not None:
            self.player_bbox = self._scale_bbox_to_screen(
                detected_bbox,
                camera_frame.image,
                camera.mirror_display,
            )
            self.player_hitbox = self._shrink_bbox(
                self.player_bbox,
                _PLAYER_HITBOX_RATIO,
            )
        else:
            self.player_bbox = None
            self.player_hitbox = None

        for ghost in self.ghosts:
            self._move_ghost(ghost, dt)

            if self.player_hitbox and self._collides(self.player_hitbox, ghost["bbox"]):
                return "game_over"

        if self.survive_time >= self.clear_time:
            return "ending"

        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"):
            return None

        camera = services.get("camera")

        if self.current_frame and camera is not None:
            surface = camera.to_surface(self.current_frame.image)
            surface = pygame.transform.scale(
                surface,
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
            )
            screen.blit(surface, (0, 0))
        else:
            screen.fill((0, 0, 0))

        if self.player_hitbox:
            pygame.draw.rect(screen, (0, 255, 0), self._to_rect(self.player_hitbox), 3)

        for ghost in self.ghosts:
            rect = self._to_rect(ghost["bbox"])
            ghost_img = pygame.transform.scale(
                self._get_ghost_image(),
                (rect.width, rect.height),
            )
            screen.blit(ghost_img, rect)

        font = pygame.font.Font(config.FONT_PATH, 36)
        text = font.render(
            f"TIME: {max(0, int(self.clear_time - self.survive_time))}",
            True,
            (255, 255, 255),
        )
        screen.blit(text, (30, 30))
        return None

    def _to_rect(self, bbox):
        x1, y1, x2, y2 = bbox
        return pygame.Rect(x1, y1, x2 - x1, y2 - y1)

    def _collides(self, a, b):
        return self._to_rect(a).colliderect(self._to_rect(b))

    def _move_ghost(self, ghost, dt):
        x1, y1, x2, y2 = ghost["bbox"]
        vx, vy = ghost["vx"], ghost["vy"]

        x1 += vx * dt
        x2 += vx * dt
        y1 += vy * dt
        y2 += vy * dt

        if x1 <= 0 or x2 >= config.SCREEN_WIDTH:
            ghost["vx"] *= -1

        if y1 <= 0 or y2 >= config.SCREEN_HEIGHT:
            ghost["vy"] *= -1

        ghost["bbox"] = (int(x1), int(y1), int(x2), int(y2))

    def _shrink_bbox(self, bbox, ratio=0.5):
        x1, y1, x2, y2 = bbox

        w = x2 - x1
        h = y2 - y1

        dx = w * (1 - ratio) / 2
        dy = h * (1 - ratio) / 2

        return (
            int(x1 + dx),
            int(y1 + dy),
            int(x2 - dx),
            int(y2 - dy),
        )

    def _scale_bbox_to_screen(self, bbox, frame, mirror_display):
        x1, y1, x2, y2 = bbox
        frame_width, frame_height = self._get_frame_size(frame)
        if mirror_display:
            x1, x2 = frame_width - x2, frame_width - x1

        scale_x = config.SCREEN_WIDTH / frame_width
        scale_y = config.SCREEN_HEIGHT / frame_height

        return (
            int(x1 * scale_x),
            int(y1 * scale_y),
            int(x2 * scale_x),
            int(y2 * scale_y),
        )

    def _get_frame_size(self, frame):
        try:
            frame_height, frame_width = frame.shape[:2]
        except AttributeError:
            frame_height = len(frame)
            frame_width = len(frame[0]) if frame_height else config.SCREEN_WIDTH

        return max(frame_width, 1), max(frame_height, 1)

    def _get_ghost_image(self):
        if self.ghost_image is None:
            self.ghost_image = pygame.image.load(_GHOST_IMAGE_PATH).convert_alpha()
        return self.ghost_image
