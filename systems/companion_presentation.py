"""Bounded, data-backed drone poses. No movement, damage or cooldown logic."""
import math
from collections import OrderedDict
import pygame
from systems.object_catalog import definition, sprite, revision

MAX_POSES = 512
MAX_BYTES = 8 * 1024 * 1024
_poses = OrderedDict()
_revision = -1
_bytes = 0


def pose(key, time, angle=0, left=False, flash=False, alpha=255):
    global _revision, _bytes
    current = revision()
    if _revision != current:
        _poses.clear()
        _bytes = 0
        _revision = current
    spec = definition(key)
    frame = int(time * spec['fps']) % max(1, spec['frames'])
    angle = (round(angle / 5) * 5) % 360
    cache_key = (key, frame, angle, left, flash, alpha)
    if cache_key not in _poses:
        art = sprite(key, frame=frame)
        if art is None:
            return None
        if left:
            art = pygame.transform.flip(art, True, False)
        if angle:
            art = pygame.transform.rotate(art, angle)
        if flash or alpha < 255:
            art = art.copy()
            if flash:
                art.fill((45, 30, 20, 0), special_flags=pygame.BLEND_RGB_ADD)
            if alpha < 255:
                # Multiply, do not replace authored catalog opacity.
                art.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        _poses[cache_key] = art
        _bytes += art.get_pitch() * art.get_height()
        while len(_poses) > MAX_POSES or _bytes > MAX_BYTES:
            _, old = _poses.popitem(last=False)
            _bytes -= old.get_pitch() * old.get_height()
        if cache_key not in _poses:
            return art  # Oversized editor art is usable but not retained.
    _poses.move_to_end(cache_key)
    return _poses[cache_key]


def draw(surface, key, center, time, *, left=False, flash=False, cooling=False, phase=0):
    art = pose(key, time, angle=3 * math.sin(time * 3 + phase),
               left=left, flash=flash, alpha=125 if cooling else 255)
    if art is None:
        return False
    center = (round(center[0]), round(center[1] + 2 * math.sin(time * 4 + phase)))
    surface.blit(art, art.get_rect(center=center))
    return True
