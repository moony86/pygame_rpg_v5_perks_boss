import random

import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    ENEMY_SPAWN_ATTEMPTS,
    ENEMY_SPAWN_SAFE_RADIUS,
    ENEMY_SPAWN_VIEW_MARGIN,
)
from systems.room_bounds import current_room_bounds


MAP_EDGE_PADDING = 100
SPAWN_BODY_SIZE = 40
VISIBLE_SPAWN_PADDING = 260
FALLBACK_RING_EXTRA_DISTANCE = 220


class SpawnSystem:
    def __init__(self):
        pass

    def reset(self, room_number, room_type):
        """Compatibility hook; spawn timing and enemy choice belong to WaveSystem."""

    def get_spawn_position(self, camera, player_rect=None):
        return self._get_spawn_position(camera, player_rect)

    def _get_spawn_position(self, camera, player_rect=None):
        player_center = player_rect.center if player_rect is not None else None

        for _ in range(ENEMY_SPAWN_ATTEMPTS * 4):
            candidate = self._candidate_spawn_position(camera)

            if candidate is None:
                continue

            x, y = candidate
            if self._is_spawn_safe(x, y, camera, player_center):
                return x, y

        if player_center is not None:
            fallback = self._fallback_position_around_player(player_center, camera)
            if fallback is not None:
                return fallback

        return self._clamp_spawn_position(camera.offset.x - ENEMY_SPAWN_VIEW_MARGIN, camera.offset.y - ENEMY_SPAWN_VIEW_MARGIN)

    def _is_spawn_safe(self, x, y, camera, player_center=None):
        center = self._spawn_center(x, y)
        no_spawn_rect = self._no_spawn_rect(camera)

        if no_spawn_rect.collidepoint(center.x, center.y):
            return False

        if player_center is not None:
            if center.distance_squared_to(player_center) < ENEMY_SPAWN_SAFE_RADIUS * ENEMY_SPAWN_SAFE_RADIUS:
                return False

        return self._inside_spawn_bounds(x, y)

    def _fallback_position_around_player(self, player_center, camera):
        distance = ENEMY_SPAWN_SAFE_RADIUS + FALLBACK_RING_EXTRA_DISTANCE
        angle_start = random.uniform(0, 360)

        for step in range(32):
            angle = angle_start + step * (360 / 32)
            offset = pygame.Vector2(distance, 0).rotate(angle)
            x = player_center[0] + offset.x - SPAWN_BODY_SIZE / 2
            y = player_center[1] + offset.y - SPAWN_BODY_SIZE / 2
            x, y = self._clamp_spawn_position(x, y)

            if self._is_spawn_safe(x, y, camera, player_center):
                return x, y

        return None

    def _spawn_center(self, x, y):
        return pygame.Vector2(x + SPAWN_BODY_SIZE / 2, y + SPAWN_BODY_SIZE / 2)

    def _no_spawn_rect(self, camera):
        visible_rect = pygame.Rect(
            int(camera.offset.x),
            int(camera.offset.y),
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )
        return visible_rect.inflate(VISIBLE_SPAWN_PADDING, VISIBLE_SPAWN_PADDING)

    def _inside_spawn_bounds(self, x, y):
        bounds = current_room_bounds()
        return (
            bounds.left + MAP_EDGE_PADDING <= x <= bounds.right - MAP_EDGE_PADDING - SPAWN_BODY_SIZE
            and bounds.top + MAP_EDGE_PADDING <= y <= bounds.bottom - MAP_EDGE_PADDING - SPAWN_BODY_SIZE
        )

    def _clamp_spawn_position(self, x, y):
        bounds = current_room_bounds()
        max_x = bounds.right - MAP_EDGE_PADDING - SPAWN_BODY_SIZE
        max_y = bounds.bottom - MAP_EDGE_PADDING - SPAWN_BODY_SIZE
        return (
            int(max(bounds.left + MAP_EDGE_PADDING, min(max_x, x))),
            int(max(bounds.top + MAP_EDGE_PADDING, min(max_y, y))),
        )

    def _candidate_spawn_position(self, camera):
        margin = ENEMY_SPAWN_VIEW_MARGIN
        side = random.choice(["top", "bottom", "left", "right"])
        bounds = current_room_bounds()

        if side == "top":
            min_x = int(camera.offset.x) - margin
            max_x = int(camera.offset.x + SCREEN_WIDTH) + margin
            y = int(camera.offset.y) - margin

            if y < bounds.top + MAP_EDGE_PADDING:
                return None

            min_x = max(bounds.left + MAP_EDGE_PADDING, min_x)
            max_x = min(bounds.right - MAP_EDGE_PADDING - SPAWN_BODY_SIZE, max_x)

            if min_x >= max_x:
                return None

            x = random.randint(min_x, max_x)

        elif side == "bottom":
            min_x = int(camera.offset.x) - margin
            max_x = int(camera.offset.x + SCREEN_WIDTH) + margin
            y = int(camera.offset.y + SCREEN_HEIGHT) + margin

            if y > bounds.bottom - MAP_EDGE_PADDING - SPAWN_BODY_SIZE:
                return None

            min_x = max(bounds.left + MAP_EDGE_PADDING, min_x)
            max_x = min(bounds.right - MAP_EDGE_PADDING - SPAWN_BODY_SIZE, max_x)

            if min_x >= max_x:
                return None

            x = random.randint(min_x, max_x)

        elif side == "left":
            x = int(camera.offset.x) - margin
            min_y = int(camera.offset.y) - margin
            max_y = int(camera.offset.y + SCREEN_HEIGHT) + margin

            if x < bounds.left + MAP_EDGE_PADDING:
                return None

            min_y = max(bounds.top + MAP_EDGE_PADDING, min_y)
            max_y = min(bounds.bottom - MAP_EDGE_PADDING - SPAWN_BODY_SIZE, max_y)

            if min_y >= max_y:
                return None

            y = random.randint(min_y, max_y)

        else:
            x = int(camera.offset.x + SCREEN_WIDTH) + margin
            min_y = int(camera.offset.y) - margin
            max_y = int(camera.offset.y + SCREEN_HEIGHT) + margin

            if x > bounds.right - MAP_EDGE_PADDING - SPAWN_BODY_SIZE:
                return None

            min_y = max(bounds.top + MAP_EDGE_PADDING, min_y)
            max_y = min(bounds.bottom - MAP_EDGE_PADDING - SPAWN_BODY_SIZE, max_y)

            if min_y >= max_y:
                return None

            y = random.randint(min_y, max_y)

        return x, y
