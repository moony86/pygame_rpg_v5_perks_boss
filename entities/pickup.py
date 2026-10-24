import random

import pygame

from systems.room_bounds import current_room_bounds
from systems.asset_loader import load_sheet_frames
from systems.object_catalog import draw_object


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
        self.previous_pos = self.pos.copy()
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
        if pickup_type not in ("gold", "xp"):
            return []
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
        self.previous_pos = self.pos.copy()
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
        if self.pickup_type in ('gold','xp') and self.magnetized_time>0:
            from systems.pickup_presentation import draw_magnet_trail
            draw_magnet_trail(surface,camera,self)
        screen_rect = camera.apply_rect(self.rect)
        if self.pickup_type == 'gold':
            from systems.object_catalog import sprite, definition
            art = sprite('visual_gold',frame=int(self.age*definition('visual_gold')['fps']))
            if art is not None:
                surface.blit(art,art.get_rect(center=screen_rect.center))
                return
        if self.pickup_type == 'xp':
            from systems.object_catalog import sprite, definition
            tier = self.tier_id if self.tier_id and self.tier_id.startswith('xp_tier_') else 'xp_tier_1'
            art = sprite('visual_'+tier,frame=int(self.age*definition('visual_'+tier)['fps']))
            if art is not None:
                surface.blit(art,art.get_rect(center=screen_rect.center))
                return
        if self.pickup_type in ('heal_potion', 'time_stop') and draw_object(surface, self.pickup_type, screen_rect.center, self.age):
            return
        frames = self.frames_for(self.pickup_type)
        if frames:
            frame_index = int(self.age * PICKUP_ANIMATION_FPS) % len(frames)
            frame = frames[frame_index]
            surface.blit(frame, frame.get_rect(center=screen_rect.center))
            return

        if self.pickup_type == "heal_potion":
            pulse = 1.0 + 0.10 * abs(pygame.math.Vector2(1, 0).rotate(self.age * 220).x)
            if self.value <= 15:
                fill_col, neck_col, aura_col = (95, 220, 105), (255, 150, 150), (30, 80, 36)
            elif self.value <= 25:
                fill_col, neck_col, aura_col = (70, 235, 135), (255, 115, 130), (28, 85, 42)
            else:
                fill_col, neck_col, aura_col = (55, 250, 170), (255, 75, 105), (18, 95, 55)
            pygame.draw.circle(surface, aura_col, screen_rect.center, round(screen_rect.width * 0.58 * pulse))
            bottle = screen_rect.inflate(-10, -6)
            neck = pygame.Rect(0, 0, max(8, screen_rect.width // 3), 9)
            neck.midbottom = (screen_rect.centerx, bottle.top + 5)
            pygame.draw.rect(surface, neck_col, neck, border_radius=3)
            pygame.draw.rect(surface, fill_col, bottle, border_radius=7)
            pygame.draw.rect(surface, (25, 120, 60), bottle, 2, border_radius=7)
            heart = [
                (screen_rect.centerx, screen_rect.centery + 7),
                (screen_rect.centerx - 9, screen_rect.centery - 1),
                (screen_rect.centerx - 5, screen_rect.centery - 8),
                (screen_rect.centerx, screen_rect.centery - 4),
                (screen_rect.centerx + 5, screen_rect.centery - 8),
                (screen_rect.centerx + 9, screen_rect.centery - 1),
            ]
            pygame.draw.polygon(surface, (255, 245, 245), heart)
            pygame.draw.line(surface, (255, 95, 110), (screen_rect.centerx - 6, screen_rect.centery), (screen_rect.centerx + 6, screen_rect.centery), 2)
            pygame.draw.line(surface, (255, 95, 110), (screen_rect.centerx, screen_rect.centery - 6), (screen_rect.centerx, screen_rect.centery + 6), 2)
            return
        if self.pickup_type == "time_stop":
            color = (120, 210, 255)
            pygame.draw.circle(surface, (16, 34, 70), screen_rect.center, max(5, screen_rect.width // 2))
            pygame.draw.circle(surface, color, screen_rect.center, max(4, screen_rect.width // 2 - 5), 2)
            pygame.draw.line(surface, color, screen_rect.center, (screen_rect.centerx, screen_rect.centery - 8), 2)
            pygame.draw.line(surface, color, screen_rect.center, (screen_rect.centerx + 7, screen_rect.centery + 4), 2)
            return

        color = (255, 215, 80) if self.pickup_type == "gold" else (110, 220, 255)
        pygame.draw.circle(surface, color, screen_rect.center, max(4, screen_rect.width // 2))
