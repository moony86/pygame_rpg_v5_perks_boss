import pygame
from settings import WHITE, YELLOW, RED, GOLD, CYAN
from systems.asset_loader import load_image


BLADE_HIT_VFX_SIZE = (42, 42)
BLADE_IMPACT_VFX_SIZE = (56, 56)


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


class SpriteEffect:
    def __init__(self, image, pos, life=0.18, start_scale=0.85, end_scale=1.25, angle=0.0):
        self.image = image
        self.pos = pygame.Vector2(pos)
        self.life = life
        self.max_life = life
        self.start_scale = start_scale
        self.end_scale = end_scale
        self.angle = angle
        self.alive = image is not None

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface, camera):
        if self.image is None:
            return
        progress = 1.0 - max(0.0, self.life / max(0.001, self.max_life))
        scale = self.start_scale + (self.end_scale - self.start_scale) * progress
        alpha = int(230 * (1.0 - progress))
        image = pygame.transform.rotozoom(self.image, self.angle, scale)
        image.set_alpha(alpha)
        pos = camera.apply_pos(self.pos)
        rect = image.get_rect(center=(round(pos.x), round(pos.y)))
        surface.blit(image, rect)


class EffectsSystem:
    _blade_hit_image = None
    _blade_impact_image = None
    _blade_hit_image_loaded = False
    _blade_impact_image_loaded = False

    def __init__(self):
        self.floating_texts = []
        self.rings = []
        self.sprite_effects = []
        if not EffectsSystem._blade_hit_image_loaded:
            EffectsSystem._blade_hit_image = load_image("engineer/blade_hit.png", size=BLADE_HIT_VFX_SIZE)
            EffectsSystem._blade_hit_image_loaded = True
        if not EffectsSystem._blade_impact_image_loaded:
            EffectsSystem._blade_impact_image = load_image("engineer/blade_impact.png", size=BLADE_IMPACT_VFX_SIZE)
            EffectsSystem._blade_impact_image_loaded = True

    def reset(self):
        self.floating_texts.clear()
        self.rings.clear()
        self.sprite_effects.clear()

    def damage_number(self, amount, pos, critical=False):
        color = GOLD if critical else WHITE
        text = f"{amount}!" if critical else str(amount)
        self.floating_texts.append(FloatingText(text, pos, color=color))

    def message(self, text, pos, color=CYAN):
        self.floating_texts.append(FloatingText(text, pos, color=color, life=1.0))

    def ring(self, pos, color=YELLOW, radius=80, life=0.45, width=3):
        self.rings.append(RingEffect(pos, color=color, max_radius=radius, life=life, width=width))

    def blade_hit(self, pos, strong=False):
        image = EffectsSystem._blade_impact_image if strong else EffectsSystem._blade_hit_image
        if image is None:
            self.ring(pos, color=(255, 230, 85) if strong else YELLOW, radius=42 if strong else 32, life=0.16, width=3 if strong else 2)
            return
        self.sprite_effects.append(SpriteEffect(
            image,
            pos,
            life=0.20 if strong else 0.14,
            start_scale=0.8 if strong else 0.75,
            end_scale=1.25 if strong else 1.05,
        ))

    def update(self, dt):
        for fx in self.floating_texts:
            fx.update(dt)
        for ring in self.rings:
            ring.update(dt)
        for sprite in self.sprite_effects:
            sprite.update(dt)
        self.floating_texts = [fx for fx in self.floating_texts if fx.alive]
        self.rings = [ring for ring in self.rings if ring.alive]
        self.sprite_effects = [sprite for sprite in self.sprite_effects if sprite.alive]

    def draw(self, surface, camera, font):
        for ring in self.rings:
            ring.draw(surface, camera)
        for sprite in self.sprite_effects:
            sprite.draw(surface, camera)
        for fx in self.floating_texts:
            fx.draw(surface, camera, font)
