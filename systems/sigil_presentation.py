"""Editable authored overlays; bounded, revision-aware transformations only."""
from functools import lru_cache
import pygame
from systems.object_catalog import sprite, revision


@lru_cache(maxsize=192)
def pose(key, diameter, opacity, angle, visual_revision):
    source = sprite(key, size=(diameter, diameter))
    if source is None:
        return None
    image = pygame.transform.rotate(source, angle)
    base_alpha = source.get_alpha()
    image.set_alpha(round(opacity * (255 if base_alpha is None else base_alpha) / 255))
    return image


def draw(surface, key, center, diameter, opacity=220, angle=0):
    diameter = max(8, min(1024, round(diameter / 4) * 4))
    opacity = max(0, min(255, round(opacity / 16) * 16))
    image = pose(key, diameter, opacity, round(angle / 5) * 5, revision())
    if image is not None:
        surface.blit(image, image.get_rect(center=center))
