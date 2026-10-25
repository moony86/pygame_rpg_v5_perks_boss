"""Bounded cached authored speed wake; no per-frame image decoding."""
from functools import lru_cache
import pygame
from systems.object_catalog import sprite, revision


@lru_cache(maxsize=96)
def wake(angle, opacity, visual_revision):
    source = sprite('fx_speed_wake')
    if source is None:
        return None
    image = pygame.transform.rotate(source, -angle)
    image.set_alpha(opacity)
    return image


def update(player, dt, previous_center):
    trails = [(pos, angle, life-dt) for pos, angle, life
              in getattr(player, '_speed_wakes', ()) if life > dt]
    delta = pygame.Vector2(player.rect.center)-previous_center
    # Discard old scene positions; never join a teleport with a giant streak.
    if delta.length_squared() > 160**2 or player.ghost_timer <= 0:
        trails = []
    elif delta.length_squared() > 0:
        clock = getattr(player, '_speed_wake_clock', 0.) + dt
        if clock >= .04:
            direction = delta.normalize()
            angle = round(pygame.Vector2(1,-1).angle_to(-direction)/15)*15 % 360
            trails.append((pygame.Vector2(player.rect.center)-direction*14, angle, .20))
            clock %= .04
        player._speed_wake_clock = clock
    player._speed_wakes = trails[-6:]


def draw(surface, camera, player):
    if player.ghost_timer <= 0:
        return
    for pos, angle, life in getattr(player, '_speed_wakes', ()):
        opacity = max(0, min(160, round(life/.20*160/32)*32))
        image = wake(angle, opacity, revision())
        if image:
            surface.blit(image, image.get_rect(center=camera.apply_pos(pos)))
