import pygame
from settings import ENEMY_BULLET_SPEED, ENEMY_BULLET_LIFETIME, ORANGE


class EnemyBullet:
    def __init__(self, x, y, direction, damage, speed=None):
        self.pos = pygame.Vector2(x, y)
        self.previous_pos = self.pos.copy()
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.radius = 6
        self.rect = pygame.Rect(x - self.radius, y - self.radius, self.radius * 2, self.radius * 2)
        self.speed = speed or ENEMY_BULLET_SPEED
        self.damage = damage
        self.remaining_life = ENEMY_BULLET_LIFETIME
        self.alive = True

    def update(self, dt):
        self.previous_pos = self.pos.copy()
        self.pos += self.direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.remaining_life -= dt
        if self.remaining_life <= 0:
            self.alive = False

    def kill(self):
        self.alive = False

    def draw(self, surface, camera):
        p = camera.apply_pos(self.pos)
        prev = camera.apply_pos(self.previous_pos)
        pygame.draw.line(surface, (255, 190, 90), prev, p, 2)
        pygame.draw.circle(surface, ORANGE, (round(p.x), round(p.y)), self.radius)
