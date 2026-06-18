import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, MAP_SIZE


class Camera:
    def __init__(self):
        self.offset = pygame.Vector2(0, 0)
        self.lerp_speed = 9.0

    def reset(self, target_rect):
        self.offset.x = target_rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = target_rect.centery - SCREEN_HEIGHT / 2
        self._clamp()

    def follow(self, target_rect, target_velocity, dt):
        look_ahead = pygame.Vector2(target_velocity) * 0.09
        target_offset = pygame.Vector2(target_rect.centerx - SCREEN_WIDTH / 2, target_rect.centery - SCREEN_HEIGHT / 2) + look_ahead
        factor = min(1.0, self.lerp_speed * dt)
        self.offset += (target_offset - self.offset) * factor
        self._clamp()

    def screen_to_world(self, pos):
        return pygame.Vector2(pos[0] + self.offset.x, pos[1] + self.offset.y)

    def _clamp(self):
        self.offset.x = max(0, min(self.offset.x, MAP_SIZE - SCREEN_WIDTH))
        self.offset.y = max(0, min(self.offset.y, MAP_SIZE - SCREEN_HEIGHT))

    def apply_rect(self, rect):
        return pygame.Rect(round(rect.x - self.offset.x), round(rect.y - self.offset.y), rect.width, rect.height)

    def apply_pos(self, pos):
        return pygame.Vector2(pos.x - self.offset.x, pos.y - self.offset.y)
