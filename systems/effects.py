import pygame
from settings import WHITE, YELLOW, RED, GOLD, CYAN


class FloatingText:
    def __init__(self, text, pos, color=WHITE, life=0.75):
        self.text = str(text)
        self.pos = pygame.Vector2(pos)
        self.color = color
        self.life = life
        self.max_life = life
        self.alive = True

    def update(self, dt):
        self.life -= dt
        self.pos.y -= 45 * dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface, camera, font):
        p = camera.apply_pos(self.pos)
        surf = font.render(self.text, True, self.color)
        surface.blit(surf, (round(p.x), round(p.y)))


class RingEffect:
    def __init__(self, pos, color=YELLOW, max_radius=80, life=0.45, width=3):
        self.pos = pygame.Vector2(pos)
        self.color = color
        self.max_radius = max_radius
        self.life = life
        self.max_life = life
        self.width = width
        self.alive = True

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface, camera):
        progress = 1 - self.life / self.max_life
        radius = int(self.max_radius * progress)
        p = camera.apply_pos(self.pos)
        if radius > 0:
            pygame.draw.circle(surface, self.color, (round(p.x), round(p.y)), radius, self.width)


class EffectsSystem:
    def __init__(self):
        self.floating_texts = []
        self.rings = []

    def reset(self):
        self.floating_texts.clear()
        self.rings.clear()

    def damage_number(self, amount, pos, critical=False):
        color = GOLD if critical else WHITE
        text = f"{amount}!" if critical else str(amount)
        self.floating_texts.append(FloatingText(text, pos, color=color))

    def message(self, text, pos, color=CYAN):
        self.floating_texts.append(FloatingText(text, pos, color=color, life=1.0))

    def ring(self, pos, color=YELLOW, radius=80, life=0.45, width=3):
        self.rings.append(RingEffect(pos, color=color, max_radius=radius, life=life, width=width))

    def update(self, dt):
        for fx in self.floating_texts:
            fx.update(dt)
        for ring in self.rings:
            ring.update(dt)
        self.floating_texts = [fx for fx in self.floating_texts if fx.alive]
        self.rings = [ring for ring in self.rings if ring.alive]

    def draw(self, surface, camera, font):
        for ring in self.rings:
            ring.draw(surface, camera)
        for fx in self.floating_texts:
            fx.draw(surface, camera, font)
