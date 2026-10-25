import pygame
from settings import PROJECTILE_LIFETIME, YELLOW, PROJECTILE_SPEED
from systems.asset_loader import load_image
from systems.object_catalog import sprite as visual_sprite, definition as visual_definition


class Projectile:
    _bullet_image = None

    def __init__(
        self,
        x,
        y,
        direction,
        damage,
        speed=None,
        pierce=0,
        critical=False,
        knockback=0,
        explosive=False,
        explosion_radius=95,
        explosion_splash_ratio=1 / 3,
        source="player",
    ):
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
        self.knockback       = knockback
        self.explosive       = explosive
        self.explosion_radius = explosion_radius
        self.explosion_splash_ratio = explosion_splash_ratio
        self.source          = source
        self.alive           = True
        self.hit_ids         = set()
        self.anim_time       = 0.0
        self.visual_trail = []
        self.visual_style = None
        self.class_visual = ''
        self._body_signature = None
        self._body_image = None

        if Projectile._bullet_image is None:
            Projectile._bullet_image = load_image("bullet.png")

    def update(self, dt):
        self.previous_pos = self.pos.copy()
        self.pos += self.direction * self.speed * dt
        from systems.shot_presentation import record_trail
        record_trail(self,dt)
        self.rect.center  = (round(self.pos.x), round(self.pos.y))
        self.remaining_life -= dt
        self.anim_time += dt
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
        from systems.shot_presentation import draw_trail,visible
        if not visible(surface,camera,self):
            return
        from systems.class_weapon_presentation import draw_projectile
        if draw_projectile(surface, camera, self):
            return
        draw_trail(surface,camera,self)
        key = ('bullet_drone' if self.source == 'engineer_drone' else
               'bullet_shuriken' if self.source == 'ninja_shuriken' else
               'bullet_explosive' if self.explosive else
               'bullet_drone' if self.visual_style == 'magic' else
               'bullet_critical' if self.critical else 'bullet_player')
        from systems.object_catalog import revision
        config=visual_definition(key)
        frame=int(pygame.time.get_ticks()/1000*config['fps'])%config['frames']
        signature=(key,frame,self.direction.x,self.direction.y,revision())
        if signature==self._body_signature:
            art=self._body_image
        else:
            art=visual_sprite(key,frame=frame)
            if art is not None:
                art=pygame.transform.rotate(art,-self.direction.as_polar()[1])
            self._body_signature=signature
            self._body_image=art
        if art is not None:
            surface.blit(art,art.get_rect(center=camera.apply_pos(self.pos)))
            return
        if self._draw_sprite(surface, camera):
            return

        p    = camera.apply_pos(self.pos)
        prev = camera.apply_pos(self.previous_pos)

        px, py = round(p.x), round(p.y)

        if self.source == "engineer_drone":
            pygame.draw.line(surface, (90, 210, 255), prev, p, 3)
            pygame.draw.circle(surface, (50, 130, 210), (px, py), self.radius + 2)
            pygame.draw.circle(surface, (230, 250, 255), (px, py), max(2, self.radius - 1))
        elif self.source == "ninja_shuriken":
            pygame.draw.line(surface, (160, 230, 255), prev, p, 2)
            r = self.radius + 2
            pts = [(px, py - r), (px + r, py), (px, py + r), (px - r, py)]
            pygame.draw.polygon(surface, (150, 235, 255), pts)
            pygame.draw.polygon(surface, (25, 65, 90), pts, 1)
        elif self.explosive:
            pygame.draw.line(surface, (255, 90, 20), prev, p, 4)
            pygame.draw.circle(surface, (255, 120, 30), (px, py), self.radius + 3)
            pygame.draw.circle(surface, (255, 235, 120), (px, py), max(2, self.radius - 1))
        elif self.critical:
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

    def _draw_sprite(self, surface, camera):
        image = None

        if self.source == "player" and not self.critical and not self.explosive:
            image = Projectile._bullet_image

        if image is None:
            return False

        angle = -self.direction.as_polar()[1]
        rotated = pygame.transform.rotate(image, angle)
        p = camera.apply_pos(self.pos)
        rect = rotated.get_rect(center=(round(p.x), round(p.y)))
        surface.blit(rotated, rect)
        return True
