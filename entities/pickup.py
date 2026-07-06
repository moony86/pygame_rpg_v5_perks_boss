import random

import pygame

from systems.room_bounds import current_room_bounds
from systems.asset_loader import load_sheet_frames


PICKUP_SIZE = (32, 32)
PICKUP_FRAME_SIZE = (32, 32)
PICKUP_FRAME_COUNT = 6
PICKUP_ANIMATION_FPS = 10
PICKUP_MAGNET_DELAY = 0.28
PICKUP_FRICTION = 7.5
PICKUP_COLLECT_DISTANCE = 18
PICKUP_FINAL_COLLECT_DISTANCE = 28
PICKUP_CLOSE_DAMPING_DISTANCE = 58
PICKUP_MAX_MAGNET_SPEED = 760
PICKUP_FORCE_DIRECT_AFTER = 1.15


class Pickup:
    _frames = {}

    def __init__(self, x, y, pickup_type, value, tier_id=None):
        self.pickup_type = pickup_type
        self.value = value
        self.tier_id = tier_id
        self.rect = pygame.Rect(0, 0, *PICKUP_SIZE)
        self.rect.center = (round(x), round(y))
        self.pos = pygame.Vector2(self.rect.center)
        angle = random.uniform(0, 360)
        speed = random.uniform(95, 180)
        self.velocity = pygame.Vector2(1, 0).rotate(angle) * speed
        self.age = 0.0
        self.alive = True
        self.spin = random.uniform(0, 6.28)
        self.force_collect = False
        self.magnetized_time = 0.0

    @classmethod
    def frames_for(cls, pickup_type):
        if pickup_type not in cls._frames:
            filename = "coin.png" if pickup_type == "gold" else "xp.png"
            cls._frames[pickup_type] = load_sheet_frames(
                filename,
                PICKUP_FRAME_SIZE,
                max_frames=PICKUP_FRAME_COUNT,
                scale=PICKUP_SIZE,
            )
        return cls._frames[pickup_type]

    def update(self, dt, player, magnet_radius):
        self.age += dt
        player_center = pygame.Vector2(player.rect.center)
        to_player = player_center - self.pos
        distance = to_player.length()

        if distance <= PICKUP_FINAL_COLLECT_DISTANCE or self.rect.colliderect(player.rect):
            self.alive = False
            return True

        magnetized = False
        if self.force_collect and distance > 0:
            magnetized = True
            direction = to_player.normalize()
            pull = direction * 1800
            self.velocity += pull * dt
        elif self.age >= PICKUP_MAGNET_DELAY and 0 < distance and (distance <= magnet_radius or self.magnetized_time > 0):
            magnetized = True
            direction = to_player.normalize()
            pull = direction * (520 + max(0, magnet_radius - distance) * 5.0)
            self.velocity += pull * dt
        else:
            damping = max(0.0, 1.0 - PICKUP_FRICTION * dt)
            self.velocity *= damping

        if magnetized:
            self.magnetized_time += dt
            direction = to_player.normalize() if distance > 0 else pygame.Vector2(0, 0)
            if distance <= PICKUP_CLOSE_DAMPING_DISTANCE:
                desired_speed = max(180, distance * 7.0)
                self.velocity = self.velocity.lerp(direction * desired_speed, min(1.0, dt * 10.0))
            elif self.magnetized_time >= PICKUP_FORCE_DIRECT_AFTER:
                self.velocity = direction * PICKUP_MAX_MAGNET_SPEED
            if self.velocity.length() > PICKUP_MAX_MAGNET_SPEED:
                self.velocity.scale_to_length(PICKUP_MAX_MAGNET_SPEED)
        else:
            self.magnetized_time = 0.0

        self.pos += self.velocity * dt
        bounds = current_room_bounds()
        self.pos.x = max(bounds.left + self.rect.width / 2, min(bounds.right - self.rect.width / 2, self.pos.x))
        self.pos.y = max(bounds.top + self.rect.height / 2, min(bounds.bottom - self.rect.height / 2, self.pos.y))
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        final_distance = (player_center - self.pos).length()
        if self.rect.colliderect(player.rect) or final_distance <= PICKUP_COLLECT_DISTANCE:
            self.alive = False
            return True
        return False

    def draw(self, surface, camera):
        screen_rect = camera.apply_rect(self.rect)
        frames = self.frames_for(self.pickup_type)
        if frames:
            frame_index = int(self.age * PICKUP_ANIMATION_FPS) % len(frames)
            frame = frames[frame_index]
            surface.blit(frame, frame.get_rect(center=screen_rect.center))
            return

        color = (255, 215, 80) if self.pickup_type == "gold" else (110, 220, 255)
        pygame.draw.circle(surface, color, screen_rect.center, max(4, screen_rect.width // 2))
