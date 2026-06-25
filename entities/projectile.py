import pygame
from settings import PROJECTILE_LIFETIME, YELLOW, PROJECTILE_SPEED


class Projectile:
    def __init__(self, x, y, direction, damage, speed=None, pierce=0, critical=False):
        self.pos          = pygame.Vector2(x, y)
        self.previous_pos = self.pos.copy()
        self.direction    = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.radius          = 6 if critical else 5
        self.rect            = pygame.Rect(x - self.radius, y - self.radius,
                                           self.radius * 2, self.radius * 2)
        self.speed           = speed or PROJECTILE_SPEED
        self.remaining_life  = PROJECTILE_LIFETIME
        self.damage          = damage
        self.pierce_remaining = pierce
        self.critical        = critical
        self.alive           = True
        self.hit_ids         = set()

    def update(self, dt):
        self.previous_pos = self.pos.copy()
        self.pos += self.direction * self.speed * dt
        self.rect.center  = (round(self.pos.x), round(self.pos.y))
        self.remaining_life -= dt
        if self.remaining_life <= 0:
            self.alive = False

    def register_hit(self, enemy):
        self.hit_ids.add(id(enemy))
        if self.pierce_remaining > 0:
            self.pierce_remaining -= 1
        else:
            self.alive = False

    def can_hit(self, enemy):
        return id(enemy) not in self.hit_ids

    def kill(self):
        self.alive = False

    def draw(self, surface, camera):
        p    = camera.apply_pos(self.pos)
        prev = camera.apply_pos(self.previous_pos)

        px, py = round(p.x), round(p.y)

        if self.critical:
            # crit: orange diamond with bright core + long trail
            pygame.draw.line(surface, (255, 140, 20), prev, p, 3)
            # diamond shape
            r = self.radius
            pts = [(px, py - r), (px + r, py), (px, py + r), (px - r, py)]
            pygame.draw.polygon(surface, (255, 100, 20), pts)
            pygame.draw.polygon(surface, (255, 230, 120), pts, 1)
            pygame.draw.circle(surface, (255, 255, 200), (px, py), 2)
        else:
            # normal: yellow bullet with white core
            pygame.draw.line(surface, (255, 240, 120), prev, p, 2)
            pygame.draw.circle(surface, YELLOW, (px, py), self.radius)
            pygame.draw.circle(surface, (255, 255, 240), (px, py), max(1, self.radius - 2))
