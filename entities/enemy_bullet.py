import pygame
from settings import ENEMY_BULLET_SPEED, ENEMY_BULLET_LIFETIME, ORANGE


class EnemyBullet:
    def __init__(self, x, y, direction, damage, speed=None, homing_target=None, turn_rate=0.0, owner_id=None):
        self.pos          = pygame.Vector2(x, y)
        self.previous_pos = self.pos.copy()
        self.direction    = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.radius         = 6
        self.rect           = pygame.Rect(x - self.radius, y - self.radius,
                                          self.radius * 2, self.radius * 2)
        self.speed          = speed or ENEMY_BULLET_SPEED
        self.damage         = damage
        self.remaining_life = ENEMY_BULLET_LIFETIME
        self.alive          = True
        self.homing_target  = homing_target
        self.turn_rate      = turn_rate
        self.owner_id       = owner_id

    def update(self, dt):
        self.previous_pos = self.pos.copy()
        if self.homing_target is not None and self.turn_rate > 0:
            target = pygame.Vector2(self.homing_target.rect.center)
            desired = target - self.pos
            if desired.length_squared() > 0:
                desired = desired.normalize()
                blend = min(1.0, self.turn_rate * dt)
                self.direction = self.direction.lerp(desired, blend)
                if self.direction.length_squared() > 0:
                    self.direction = self.direction.normalize()

        self.pos         += self.direction * self.speed * dt
        self.rect.center  = (round(self.pos.x), round(self.pos.y))
        self.remaining_life -= dt
        if self.remaining_life <= 0:
            self.alive = False

    def kill(self):
        self.alive = False

    def draw(self, surface, camera):
        p    = camera.apply_pos(self.pos)
        prev = camera.apply_pos(self.previous_pos)

        px, py = round(p.x), round(p.y)

        # danger red/orange spike – longer trail, angular tip
        pygame.draw.line(surface, (200, 80, 0), prev, p, 3)

        body_col = (255, 70, 210) if self.turn_rate > 0 else ORANGE
        core_col = (120, 0, 90) if self.turn_rate > 0 else (100, 20, 0)

        # body circle
        pygame.draw.circle(surface, body_col, (px, py), self.radius)

        # inner dark core (sinister look)
        pygame.draw.circle(surface, core_col, (px, py), self.radius - 2)

        # hot tip in direction of travel
        tip = p + self.direction * (self.radius + 2)
        pygame.draw.circle(surface, (255, 200, 80), (round(tip.x), round(tip.y)), 3)
