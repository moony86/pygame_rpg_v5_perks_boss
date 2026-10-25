import math

import pygame
from settings import WHITE, YELLOW, RED, GOLD, CYAN
from systems.asset_loader import load_image
from systems.object_catalog import sprite as visual_sprite, definition as visual_definition


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
        self.visual_key = 'fx_explosion' if color[0]>200 and color[1]<170 else 'fx_ring'
        self.life = life*visual_definition(self.visual_key)['life']/.45
        self.max_life = self.life
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
        key = self.visual_key
        art = visual_sprite(key,frame=int((self.max_life-self.life)*visual_definition(key)['fps']))
        if art is not None and radius > 0:
            art = pygame.transform.scale(art,(max(2,radius*2),max(2,radius*2))).copy()
            art.fill(self.color,special_flags=pygame.BLEND_RGB_MULT)
            art.set_alpha(round(210*(1-progress)*visual_definition(key)['opacity']/255))
            surface.blit(art,art.get_rect(center=p))
            return
        if radius > 0:
            pygame.draw.circle(surface, self.color, (round(p.x), round(p.y)), radius, self.width)


class TimeStopWaveEffect(RingEffect):
    def draw(self, surface, camera):
        progress = 1 - self.life / self.max_life
        radius = int(self.max_radius * progress)
        p = camera.apply_pos(self.pos)
        if radius <= 0:
            return
        layer = getattr(self, '_draw_layer', None)
        if layer is None or layer.get_size() != surface.get_size():
            layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self._draw_layer = layer
        else:
            layer.fill((0, 0, 0, 0))
        alpha = int(150 * (1.0 - progress))
        pygame.draw.circle(layer, (*self.color, max(25, alpha)), (round(p.x), round(p.y)), radius, self.width)
        pygame.draw.circle(layer, (235, 255, 255, max(18, alpha // 2)), (round(p.x), round(p.y)), max(8, radius // 3), max(2, self.width // 2))
        surface.blit(layer, (0, 0))


class SlashEffect:
    def __init__(self, start, end, color=(165, 235, 255), life=0.16, width=7):
        self.start = pygame.Vector2(start)
        self.end = pygame.Vector2(end)
        self.color = color
        self.life = life
        self.max_life = life
        self.width = width
        self.alive = True

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface, camera):
        progress = max(0.0, min(1.0, self.life / max(0.001, self.max_life)))
        alpha = int(210 * progress)
        start = camera.apply_pos(self.start)
        end = camera.apply_pos(self.end)
        art = visual_sprite('fx_slash',frame=int((self.max_life-self.life)*visual_definition('fx_slash')['fps']))
        if art is not None:
            direction = end-start
            art = pygame.transform.scale(art,(max(8,round(direction.length())),max(12,self.width*4)))
            art = pygame.transform.rotate(art,-direction.as_polar()[1])
            art.fill(self.color,special_flags=pygame.BLEND_RGB_MULT)
            art.set_alpha(round(alpha*visual_definition('fx_slash')['opacity']/255))
            surface.blit(art,art.get_rect(center=(start+end)/2))
            return
        color = (*self.color, alpha)
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.line(layer, color, (round(start.x), round(start.y)), (round(end.x), round(end.y)), self.width)
        pygame.draw.line(layer, (255, 255, 255, min(230, alpha + 25)), (round(start.x), round(start.y)), (round(end.x), round(end.y)), max(2, self.width // 3))
        surface.blit(layer, (0, 0))


class SpriteEffect:
    def __init__(self, image, pos, life=0.18, start_scale=0.85, end_scale=1.25, angle=0.0, visual_key=None):
        self.image = image
        self.pos = pygame.Vector2(pos)
        self.life = life
        self.max_life = life
        self.start_scale = start_scale
        self.end_scale = end_scale
        self.angle = angle
        self.visual_key = visual_key
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
        source = self.image if not self.visual_key else visual_sprite(self.visual_key,
            frame=int((self.max_life-self.life)*visual_definition(self.visual_key)['fps']))
        image = pygame.transform.rotozoom(source, self.angle, scale)
        base_alpha = source.get_alpha()
        image.set_alpha(round(alpha*(255 if base_alpha is None else base_alpha)/255))
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
        self.slashes = []
        self.sprite_effects = []
        self.shot_effects = []
        from systems.shot_presentation import ShotHit
        self._shot_pool=[ShotHit.__new__(ShotHit) for _ in range(96)]
        self.collection_effects = []
        self.time_stop_overlay_timer = 0.0
        self.time_stop_overlay_duration = 0.0
        self.time_stop_release_flash = 0.0
        if not EffectsSystem._blade_hit_image_loaded:
            EffectsSystem._blade_hit_image = load_image("engineer/blade_hit.png", size=BLADE_HIT_VFX_SIZE)
            EffectsSystem._blade_hit_image_loaded = True
        if not EffectsSystem._blade_impact_image_loaded:
            EffectsSystem._blade_impact_image = load_image("engineer/blade_impact.png", size=BLADE_IMPACT_VFX_SIZE)
            EffectsSystem._blade_impact_image_loaded = True

    def reset(self):
        self.floating_texts.clear()
        self.rings.clear()
        self.slashes.clear()
        self.sprite_effects.clear()
        for hit in self.shot_effects:
            hit.alive=False
            hit.target=None
            self._shot_pool.append(hit)
        self.shot_effects.clear()
        self.collection_effects.clear()
        self.time_stop_overlay_timer = 0.0
        self.time_stop_overlay_duration = 0.0
        self.time_stop_release_flash = 0.0

    def damage_number(self, amount, pos, critical=False):
        color = GOLD if critical else WHITE
        text = f"{amount}!" if critical else str(amount)
        self.floating_texts.append(FloatingText(text, pos, color=color))

    def collect_pickup(self,kind,value,pos):
        from systems.pickup_presentation import CollectPulse,KINDS
        if kind not in KINDS:
            return
        for pulse in reversed(self.collection_effects):
            if pulse.kind==kind and pulse.alive and pulse.age<.18:
                pulse.merge(value,pos)
                return
        # One visible pulse per kind; a new batch replaces the fading old batch.
        self.collection_effects=[pulse for pulse in self.collection_effects if pulse.kind!=kind]
        self.collection_effects.append(CollectPulse(kind,value,pos))

    def impact(self, pos, critical=False):
        image = visual_sprite('fx_impact')
        if image is not None:
            self.sprite_effects.append(SpriteEffect(image, pos,
                life=visual_definition('fx_impact')['life'], end_scale=1.35 if critical else 1.05, visual_key='fx_impact'))

    def explosion(self, pos, radius):
        """World-space blast independent of the returning companion's position/state."""
        image = visual_sprite('fx_explosion')
        if image is not None:
            scale = max(1, radius * 2) / max(image.get_size())
            self.sprite_effects.append(SpriteEffect(image, pos,
                life=max(.38, visual_definition('fx_explosion')['life']),
                start_scale=scale * .65, end_scale=scale * 1.12,
                visual_key='fx_explosion'))
        self.impact(pos, critical=True)

    def projectile_hit(self,shot,pos,target=None,shield=False):
        from systems.shot_presentation import ShotHit
        # Reuse the oldest visual at the existing cap; gameplay hits are untouched.
        hit=self._shot_pool.pop() if self._shot_pool else self.shot_effects.pop(0)
        ShotHit.__init__(hit,shot,pos,target,shield)
        self.shot_effects.append(hit)

    def chaser_death(self, enemy):
        image = visual_sprite('enemy_chaser')
        if image is not None:
            image = image.copy()
            if not getattr(enemy, 'facing_left', False):
                image = pygame.transform.flip(image, True, False)
            self.sprite_effects.append(SpriteEffect(image, enemy.rect.center,
                life=.24, start_scale=1.08, end_scale=.15, angle=18))

    def ranged_death(self, enemy):
        self.actor_death(enemy)

    def actor_death(self, enemy):
        key='enemy_'+enemy.type.name.lower()
        if enemy.type.name=='BOSS' and enemy.phase>1:
            key='enemy_boss_phase_'+str(enemy.phase)
        image=visual_sprite(key)
        if image is not None:
            image=image.copy()
            if not getattr(enemy,'facing_left',False):
                image=pygame.transform.flip(image,True,False)
            self.sprite_effects.append(SpriteEffect(image,enemy.rect.center,
                life=.28,start_scale=1.05,end_scale=.1,angle=-12))

    def message(self, text, pos, color=CYAN):
        self.floating_texts.append(FloatingText(text, pos, color=color, life=1.0))

    def ring(self, pos, color=YELLOW, radius=80, life=0.45, width=3):
        self.rings.append(RingEffect(pos, color=color, max_radius=radius,life=life,width=width))

    def slash(self, start, end, color=(165, 235, 255), life=0.16, width=7):
        self.slashes.append(SlashEffect(start, end, color=color,
            life=life*visual_definition('fx_slash')['life']/.16, width=width))

    def heal_burst(self, pos):
        self.rings.append(RingEffect(pos, color=(85, 245, 135), max_radius=58, life=0.30, width=5))
        self.rings.append(RingEffect(pos, color=(255, 105, 120), max_radius=34, life=0.22, width=3))

    def super_dash_burst(self, pos):
        self.rings.append(RingEffect(pos, color=(110, 235, 255), max_radius=118, life=0.26, width=6))
        self.rings.append(RingEffect(pos, color=(255, 255, 255), max_radius=62, life=0.16, width=4))

    def time_stop_trigger(self, pos, duration):
        self.rings.append(TimeStopWaveEffect(pos, color=(120, 220, 255), max_radius=1300, life=0.34, width=9))
        self.time_stop_overlay_timer = max(self.time_stop_overlay_timer, float(duration))
        self.time_stop_overlay_duration = max(self.time_stop_overlay_duration, float(duration))

    def airstrike_launch(self, pos, radius):
        self.rings.append(RingEffect(pos, color=(255, 205, 95), max_radius=radius, life=0.85, width=2))
        self.rings.append(RingEffect(pos, color=(255, 90, 45), max_radius=max(30, radius // 2), life=0.55, width=3))
        self.message("MISSILE INBOUND", pos, color=(255, 205, 95))

    def airstrike_impact(self, pos, radius):
        self.explosion(pos, radius)
        for scale, color, life, width in (
            (0.35, (255, 255, 190), 0.18, 5),
            (0.70, (255, 155, 65), 0.30, 5),
            (1.00, (255, 75, 45), 0.46, 6),
            (1.45, (255, 215, 95), 0.62, 3),
        ):
            self.rings.append(RingEffect(pos, color=color, max_radius=round(radius * scale), life=life, width=width))
        self.message("SIEGE WAVE", pos, color=(255, 190, 80))

    def draw_dash_charge(self, surface, camera, pos, ratio):
        ratio = max(0.0, min(1.0, ratio))
        if ratio <= 0.0:
            return
        p = camera.apply_pos(pygame.Vector2(pos))
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.026)
        radius = round(30 + 42 * ratio + 5 * pulse)
        from systems.sigil_presentation import draw
        draw(surface, 'fx_dash_charge', p, radius * 2, 100 + 140 * ratio)

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
        for slash in self.slashes:
            slash.update(dt)
        for sprite in self.sprite_effects:
            sprite.update(dt)
        for hit in self.shot_effects:
            hit.update(dt)
        for pulse in self.collection_effects:
            pulse.update(dt)
        was_time_stopped = self.time_stop_overlay_timer > 0
        if self.time_stop_overlay_timer > 0:
            self.time_stop_overlay_timer = max(0.0, self.time_stop_overlay_timer - dt)
        if was_time_stopped and self.time_stop_overlay_timer <= 0:
            self.time_stop_release_flash = 0.18
        if self.time_stop_release_flash > 0:
            self.time_stop_release_flash = max(0.0, self.time_stop_release_flash - dt)
        self.floating_texts = [fx for fx in self.floating_texts if fx.alive]
        self.rings = [ring for ring in self.rings if ring.alive]
        self.slashes = [slash for slash in self.slashes if slash.alive]
        self.sprite_effects = [sprite for sprite in self.sprite_effects if sprite.alive]
        live_hits=[]
        for hit in self.shot_effects:
            if hit.alive:
                live_hits.append(hit)
            else:
                hit.target=None
                self._shot_pool.append(hit)
        self.shot_effects=live_hits
        self.collection_effects=[pulse for pulse in self.collection_effects if pulse.alive]

    def draw(self, surface, camera, font):
        self.draw_time_stop_overlay(surface)
        for ring in self.rings:
            ring.draw(surface, camera)
        for slash in self.slashes:
            slash.draw(surface, camera)
        for sprite in self.sprite_effects:
            sprite.draw(surface, camera)
        for hit in self.shot_effects:
            hit.draw(surface,camera)
        for fx in self.floating_texts:
            fx.draw(surface, camera, font)
        from systems.pickup_presentation import KINDS
        for row,pulse in enumerate(sorted(self.collection_effects,key=lambda item:KINDS.index(item.kind))):
            pulse.draw(surface,camera,font,row=row)

    def draw_time_stop_overlay(self, surface):
        from systems.time_stop_presentation import draw
        draw(surface, self.time_stop_overlay_timer, self.time_stop_overlay_duration,
             self.time_stop_release_flash)
