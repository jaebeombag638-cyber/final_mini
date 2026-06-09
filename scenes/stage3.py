import pygame

import config
from core.scene import Scene
from scenes.global_rules import apply_global_rules


class Stage3Scene(Scene):
    def __init__(self):
        self.player_bbox = None
        self.player_hitbox = None  
        self.ghosts = [
        {"bbox": (20, 20, 80, 80), "vx": 120, "vy": 90},
        {
        "bbox": (
            config.SCREEN_WIDTH - 80,
            config.SCREEN_HEIGHT - 80,
            config.SCREEN_WIDTH - 20,
            config.SCREEN_HEIGHT - 20,
        ),
        "vx": -120,
        "vy": -90,
        },
        ]
        self.survive_time = 0
        self.clear_time = 30
        self.frame_index = 0
        self.current_frame = None
        self.ghost_image = pygame.image.load("assets/images/miiya-halloween-4451903_640.png").convert_alpha()

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        self.frame_index += 1
        self.survive_time += dt

        rule_result = apply_global_rules(
            dt=dt,
            now=pygame.time.get_ticks() / 1000,
            game_state=game_state,
            services=services,
        )

        if rule_result:
            return rule_result

        camera = services["camera"]
        detector = services["detector"]

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
            h,w = camera_frame.image.shape[:2]

            if camera.mirror_display:
                detected_bbox = self._mirror_bbox(detected_bbox, w)

            self.player_bbox = detected_bbox
            self.player_hitbox = self._shrink_bbox(detected_bbox,0.5)
        else:
            self.player_bbox = None
            self.player_hitbox = None

        for ghost in self.ghosts:
            self._move_ghost(ghost, dt)

            if self.player_hitbox and self._collides(self.player_hitbox,ghost["bbox"]):
                return "game_over"

        if self.survive_time >= self.clear_time:
            return "ending"

        return None

    def draw(self, screen, game_state, services) -> None:
        camera = services["camera"]

        if self.current_frame:
            surface = camera.to_surface(self.current_frame.image)
            screen.blit(surface, (0, 0))
        else:
            screen.fill((0, 0, 0))

        if self.player_bbox:
            pygame.draw.rect(screen, (0, 255, 0), self._to_rect(self.player_bbox), 3)

        for ghost in self.ghosts:
            rect = self._to_rect(ghost["bbox"])

            ghost_img = pygame.transform.scale(
                self.ghost_image,
                (rect.width, rect.height)
            )

            screen.blit(ghost_img, rect)

        font = pygame.font.Font(config.FONT_PATH, 36)
        text = font.render(
            f"TIME: {max(0, int(self.clear_time - self.survive_time))}",
            True,
            (255, 255, 255),
        )
        screen.blit(text, (30, 30))

    def _to_rect(self, bbox):
        x1, y1, x2, y2 = bbox
        return pygame.Rect(x1, y1, x2 - x1, y2 - y1)
    
    def _update_player_bbox(self, detected_bbox, image):
        self.player_bbox = None
        self.player_hitbox = None

        if not detected_bbox is None:
            return
        
        self.player_bbox = detected_bbox
        self.player_hitbox = self._shrink_bbox(detected_bbox, 0.5)

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
    
    def _mirror_bbox(self, bbox, image_width):
        x1, y1, x2, y2 = bbox

        return (
            image_width - x2,
            y1,
            image_width - x1,
            y2,
        )