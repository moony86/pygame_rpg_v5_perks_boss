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


def draw(surface, camera, player):
    if player.ghost_timer<=0:
        return
    direction = player.move_direction
    if not direction.length_squared():
        direction = player.aim_direction
    angle = round((pygame.Vector2(1,-1).angle_to(-direction)) / 15)*15 % 360
    opacity = 190 if player.ghost_timer>.35 else max(0,round(player.ghost_timer/.35*190/32)*32)
    image = wake(angle,opacity,revision())
    if image:
        center = camera.apply_pos(pygame.Vector2(player.rect.center)-direction*14)
        surface.blit(image,image.get_rect(center=center))
